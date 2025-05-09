import re
import pandas as pd
import streamlit as st
import logging

# 로거 설정 (data_collector.py와 동일한 설정을 사용하거나, 필요시 다르게 설정)
# 여기서는 data_collector.py에서 이미 설정했다고 가정하고, 동일한 로거 사용
logger = logging.getLogger(__name__) 

class TableCreator:
    def __init__(self, config, merged_df, find_external_file):
        self.config = config
        self.merged_df = merged_df
        self._find_external_file = find_external_file
        # 자식 클래스에서 정의할 속성들
        self.id_column_key: str = ""       # 예: "bug_no_column"
        self.regex_key: str = ""           # 예: "bug_regex"
        self.template_key: str = ""        # 예: "bug_pattern_template"
        self.external_columns_key: str = "" # 예: "bug_file_columns"
        self.merge_how: str = ""           # 'left' 또는 'right'
        self.desired_order: list[str] = [] # 최종 컬럼 순서

    def create_table(self):
        """테이블 생성"""
        filtered_df = self._filter_data()
        pivot_df = self._create_pivot_table(filtered_df)
        external_data = self._load_external_data()
        return self._merge_and_finalize(pivot_df, external_data)

    def _filter_data(self):
        raise NotImplementedError
        
    def _create_pivot_table(self, filtered_df):
        raise NotImplementedError
        
    def _load_external_data(self):
        # 자식 클래스가 external_data를 로드하고,
        # 로드 실패 시 None을 반환하도록 구현해야 함.
        # 각 자식 클래스에 이미 구현되어 있음.
        raise NotImplementedError

    def _extract_number(self, db_no):
        """ID 컬럼 값에서 숫자 추출 (정규식 사용)"""
        if pd.isna(db_no):
            return None
        # self.regex_key는 자식 클래스에서 설정됨
        match = re.search(self.config[self.regex_key], str(db_no))
        return int(match.group(1)) if match else None

    def _merge_and_finalize(self, pivot_df, external_data):
        """
        공통 Merge 및 후처리 로직.
        입력 pivot_df와 external_data는 기본적인 전처리가 완료되었다고 가정.
        (예: external_data의 'No'는 숫자형이고 NaN 없음, 원본 'No'는 'No_original'에 있음)
        """
        id_col_name = self.config[self.id_column_key]
        test_name_col_name = self.config["test_name_column"]
        external_file_cols = self.config[self.external_columns_key]
        id_template = self.config[self.template_key]

        # 1. external_data 유효성 검사 (None 처리)
        if external_data is None:
            # (기존 로직 유지)
            if self.merge_how == 'right':
                 final_cols = [id_col_name] + [col for col in external_file_cols if col != 'No'] + ["件数", test_name_col_name]
                 return pd.DataFrame(columns=final_cols)
            else: # QA
                 final_cols = [id_col_name, "件数", test_name_col_name]
                 # pivot_df에 필요한 컬럼이 없을 수 있으므로 확인 후 추가
                 for col in final_cols:
                     if col not in pivot_df.columns:
                         pivot_df[col] = 0 if col == "件数" else (None if col == id_col_name else "")
                 # external_data가 없으면 external_file_columns는 추가 X
                 if pivot_df.empty:
                     logger.warning(f"{self.__class__.__name__}: 외부 데이터가 없고 피벗 테이블도 비어 있어 빈 테이블을 반환합니다. 최종 컬럼: {final_cols}")
                     return pd.DataFrame(columns=final_cols)
                 else:
                     logger.info(f"{self.__class__.__name__}: 외부 데이터가 없어 피벗 테이블 기반으로 처리합니다. 최종 컬럼: {final_cols}")
                     return pivot_df[final_cols].copy()

        # external_data의 'No' 컬럼 숫자 변환 및 NaN 처리는 DataCollector에서 이미 수행됨
        # external_data가 비어있는 경우도 DataCollector에서 처리되어 여기서는 체크 불필요

        # 2. pivot_df 준비 (ID Number 추출)
        temp_id_number_col = 'IDNumber' # 임시 컬럼명
        if not pivot_df.empty and id_col_name in pivot_df.columns:
            pivot_df[temp_id_number_col] = pivot_df[id_col_name].apply(self._extract_number)
            pivot_df = pivot_df.dropna(subset=[temp_id_number_col]) # Regex 매칭 안된 경우 NaN 제거
            if not pivot_df.empty:
                pivot_df[temp_id_number_col] = pivot_df[temp_id_number_col].astype(int)
        else:
            # pivot_df가 비거나 id_col_name이 없으면 빈 DF로 초기화
             pivot_df = pd.DataFrame(columns=[id_col_name, '件数', test_name_col_name, temp_id_number_col])


        # 3. Merge 수행
        # external_data의 'No'는 이미 숫자형임
        # pivot_df의 temp_id_number_col도 숫자형임
        merged_result = pd.merge(
            pivot_df,
            external_data, # 'No', 'No_original' 및 external_file_columns 포함
            left_on=temp_id_number_col, right_on='No', # 숫자형 ID로 조인
            how=self.merge_how,
            suffixes=('_pivot', '_external')
        )

        # 4. 컬럼 정리 및 값 채우기
        # '件数' 컬럼 처리 (기존 로직 유지)
        count_col = '件数_pivot' if '件数_pivot' in merged_result.columns else '件数'
        if count_col in merged_result.columns:
            merged_result['件数'] = merged_result[count_col].fillna(0).astype(int)
            if count_col != '件数': merged_result = merged_result.drop(columns=[count_col])
        else:
            merged_result['件数'] = 0

        # 'test_name_column' 처리 (기존 로직 유지)
        test_name_col_pivot = test_name_col_name + '_pivot'
        if test_name_col_pivot in merged_result.columns:
            merged_result[test_name_col_name] = merged_result[test_name_col_pivot].fillna('')
            merged_result = merged_result.drop(columns=[test_name_col_pivot])
        elif test_name_col_name not in merged_result.columns:
             merged_result[test_name_col_name] = ''
        else:
             merged_result[test_name_col_name] = merged_result[test_name_col_name].fillna('')

        # 'id_column' 생성/처리
        # external_data에서 온 'No_original' 컬럼은 항상 존재한다고 가정 (DataCollector에서 추가됨)
        no_original_col = 'No_original_external' if 'No_original_external' in merged_result.columns else 'No_original'
        
        if self.merge_how == 'right': # Bug: external 기준, No_original 사용
            if no_original_col in merged_result.columns:
                 merged_result[id_col_name] = merged_result[no_original_col].apply(
                     lambda no: id_template.replace("{Int}", str(int(no))) if pd.notna(no) else None
                 )
                 # No_original 사용 후 제거는 최종 컬럼 선택에서 처리
            else:
                 merged_result[id_col_name] = None
                 logger.warning(f"Could not find 'No_original' column ({no_original_col}) after merge for ID generation.")
            # 임시 IDNumber 및 external 'No' 제거 (기존 로직 유지)
            external_no_col = 'No_external' if 'No_external' in merged_result.columns else 'No'
            cols_to_drop = [temp_id_number_col + '_pivot', temp_id_number_col, external_no_col, no_original_col]

        else: # QA: pivot 기준, pivot의 id_col 사용
            id_col_pivot = id_col_name + '_pivot'
            if id_col_pivot in merged_result.columns:
                 # 숫자로 시작하는 ID 값이면 정수 변환 후 템플릿에 적용, 아니면 원본 값 사용
                 merged_result[id_col_name] = merged_result[id_col_pivot].apply(
                     lambda id_val: id_template.replace("{Int}", str(int(float(id_val)))) if pd.notna(id_val) and str(id_val).replace('.', '', 1).isdigit() else id_val
                 )
                 # ID 컬럼 이름 정리가 되었으므로 _pivot 버전 제거는 최종 단계에서 처리
            elif id_col_name not in merged_result.columns and not merged_result.empty:
                 logger.warning(f"Could not find original ID column ({id_col_name} or {id_col_pivot}) after merge.")
                 merged_result[id_col_name] = None
            # 임시 IDNumber 및 external 'No', 'No_original' 제거 (기존 로직 유지)
            external_no_col = 'No_external' if 'No_external' in merged_result.columns else 'No'
            cols_to_drop = [temp_id_number_col + '_pivot', temp_id_number_col, external_no_col, no_original_col]

        # 실제로 존재하는 임시/중복 컬럼만 제거
        merged_result = merged_result.drop(columns=[col for col in cols_to_drop if col in merged_result.columns], errors='ignore')


        # 5. 최종 컬럼 선택 및 순서 지정 (기존 로직 유지)
        final_cols_mapping = {}
        for col_name in self.desired_order:
            # external에서 온 컬럼은 _external suffix 확인
            col_suffixed_external = col_name + '_external'
            if col_name == id_col_name or col_name == '件数' or col_name == test_name_col_name:
                 if col_name in merged_result.columns: final_cols_mapping[col_name] = col_name
            elif col_suffixed_external in merged_result.columns:
                 final_cols_mapping[col_name] = col_suffixed_external
            elif col_name in merged_result.columns: # suffix 없이 external에서 온 경우
                final_cols_mapping[col_name] = col_name

        final_cols_existing_suffixed = [final_cols_mapping[col] for col in self.desired_order if col in final_cols_mapping]

        if not final_cols_existing_suffixed:
             return pd.DataFrame(columns=self.desired_order)

        merged_result = merged_result[final_cols_existing_suffixed].copy()
        merged_result.columns = [col.replace('_external', '') for col in merged_result.columns]

        # 6. 건수가 0인 행 제외 (기존 로직 유지)
        if '件数' in merged_result.columns:
             merged_result = merged_result[merged_result['件数'] > 0].copy()

        return merged_result


class BugTableCreator(TableCreator):
    def __init__(self, config, merged_df, find_external_file):
        super().__init__(config, merged_df, find_external_file)
        self.bug_data = None

        self.id_column_key = "bug_no_column"
        self.regex_key = "bug_regex"
        self.template_key = "bug_pattern_template"
        self.external_columns_key = "bug_file_columns"
        self.merge_how = "right"
        self.desired_order = [
            self.config[self.id_column_key],
            "JIRA#", "件数", "概要",
            self.config["test_name_column"], "ステータス"
        ]

    def _filter_data(self):
        if self.merged_df.empty or self.config["result_column"] not in self.merged_df.columns:
            return pd.DataFrame()
        return self.merged_df[self.merged_df[self.config["result_column"]].isin(['NG', 'BK'])].copy()

    def _create_pivot_table(self, filtered_df):
        """
        Bug용 Pivot 테이블 생성.
        입력 filtered_df는 전처리 완료 가정 (필수 컬럼 존재).
        """
        id_col = self.config[self.id_column_key]
        test_id_col = self.config["test_id_column"]
        test_name_col = self.config["test_name_column"]
        final_cols = [id_col, '件数', test_name_col]

        # 입력 데이터 확인 (ID 컬럼 등 존재는 DataCollector에서 보장)
        if filtered_df.empty:
            return pd.DataFrame(columns=final_cols)

        try:
            # 件数 계산 (ID 컬럼의 NaN은 pivot_table에서 자동 제외)
            pivot_count = filtered_df.pivot_table(
                index=id_col, values=test_id_col, aggfunc='count'
            ).reset_index().rename(columns={test_id_col: '件数'})

            # 試験名 목록 생성 (컬럼 없으면 빈 값으로 채워짐 - DataCollector에서 처리)
            pivot_test_names = filtered_df.groupby(id_col)[test_name_col] \
                .agg(lambda x: ', '.join(sorted(set(x.dropna().astype(str))))) \
                .reset_index()

            # 병합 (pivot_count가 기준)
            if pivot_count.empty: # NG/BK가 하나도 없는 경우
                 return pd.DataFrame(columns=final_cols)
            else:
                 merged_pivot = pd.merge(pivot_count, pivot_test_names, on=id_col, how='left')
                 merged_pivot[test_name_col] = merged_pivot[test_name_col].fillna('')
                 return merged_pivot[final_cols]

        except KeyError as e:
            # test_id_col 등이 없을 경우 (DataCollector에서 걸러지지 않았다면)
            logger.error(f"Bug ピボットテーブル作成中にエラー: 必要なカラム({e})が見つかりません。")
            st.error(f"버그 피벗 테이블 생성 중 오류가 발생했습니다. 필요한 컬럼({e})을 찾을 수 없습니다. CLI 로그를 확인하세요.")
            return pd.DataFrame(columns=final_cols)

    def _load_external_data(self):
        """
        외부 버그 목록 로드. DataCollector에서 전달받은 데이터 사용.
        (데이터는 이미 전처리 되었다고 가정)
        """
        # hasattr 체크 제거 (DataCollector에서 항상 설정 가정)
        if self.bug_data is not None:
             # 전달받은 데이터 사용 (이미 전처리됨)
             return self.bug_data.copy() # 방어적 복사
        else:
             logger.error("BugTableCreator에 내부 버그 리스트 데이터가 전달되지 않았습니다.")
             st.error("버그 테이블 생성에 필요한 내부 버그 리스트 데이터가 없습니다. CLI 로그를 확인하세요.")
             return None


class QATableCreator(TableCreator):
    def __init__(self, config, merged_df, find_external_file):
        super().__init__(config, merged_df, find_external_file)
        self.qa_data = None

        self.id_column_key = "qa_no_column"
        self.regex_key = "qa_regex"
        self.template_key = "qa_pattern_template"
        self.external_columns_key = "qa_file_columns"
        self.merge_how = "left"
        self.desired_order = [
            self.config[self.id_column_key],
            "件数", "質問者", "コメント", "回答",
            self.config["test_name_column"], "ステータス"
        ]

    def _filter_data(self):
        if self.merged_df.empty or self.config["result_column"] not in self.merged_df.columns:
            return pd.DataFrame()
        return self.merged_df[self.merged_df[self.config["result_column"]] == 'QA'].copy()

    def _create_pivot_table(self, filtered_df):
        """
        QA용 Pivot 테이블 생성.
        입력 filtered_df는 전처리 완료 가정 (필수 컬럼 존재).
        """
        id_col = self.config[self.id_column_key]
        test_id_col = self.config["test_id_column"]
        test_name_col = self.config["test_name_column"]
        final_cols = [id_col, '件数', test_name_col]

        if filtered_df.empty:
            return pd.DataFrame(columns=final_cols)

        try:
            pivot_count = filtered_df.pivot_table(
                index=id_col, values=test_id_col, aggfunc='count'
            ).reset_index().rename(columns={test_id_col: '件数'})

            pivot_test_names = filtered_df.groupby(id_col)[test_name_col] \
                .agg(lambda x: ', '.join(sorted(set(x.dropna().astype(str))))) \
                .reset_index()

            if pivot_count.empty: # QA 결과가 하나도 없는 경우
                 return pd.DataFrame(columns=final_cols)
            else:
                 merged_pivot = pd.merge(pivot_count, pivot_test_names, on=id_col, how='left')
                 merged_pivot[test_name_col] = merged_pivot[test_name_col].fillna('')
                 return merged_pivot[final_cols]

        except KeyError as e:
             logger.error(f"QA ピボットテーブル作成中にエラー: 必要なカラム({e})が見つかりません。")
             st.error(f"QA 피벗 테이블 생성 중 오류가 발생했습니다. 필요한 컬럼({e})을 찾을 수 없습니다. CLI 로그를 확인하세요.")
             return pd.DataFrame(columns=final_cols)


    def _load_external_data(self):
        """
        외부 QA 목록 로드. DataCollector에서 전달받은 데이터 사용.
        (데이터는 이미 전처리 되었다고 가정)
        """
        if self.qa_data is not None:
             return self.qa_data.copy() # 방어적 복사
        else:
             logger.error("QATableCreator에 내부 QA 리스트 데이터가 전달되지 않았습니다.")
             st.error("QA 테이블 생성에 필요한 내부 QA 리스트 데이터가 없습니다. CLI 로그를 확인하세요.")
             return None 