import re
import pandas as pd
import streamlit as st

class TableCreator:
    def __init__(self, config, merged_df, find_external_file):
        self.config = config
        self.merged_df = merged_df
        self._find_external_file = find_external_file

    def create_table(self):
        """테이블 생성"""
        filtered_df = self._filter_data()
        pivot_df = self._create_pivot_table(filtered_df)
        external_data = self._load_external_data()
        return self._merge_data(pivot_df, external_data)

    def _filter_data(self):
        raise NotImplementedError
        
    def _create_pivot_table(self, filtered_df):
        raise NotImplementedError
        
    def _load_external_data(self):
        raise NotImplementedError
        
    def _merge_data(self, pivot_df, external_data):
        raise NotImplementedError

class BugTableCreator(TableCreator):
    def __init__(self, config, merged_df, find_external_file):
        super().__init__(config, merged_df, find_external_file)
        self.bug_data = None  # 내부 버그리스트 데이터

    def _filter_data(self):
        return self.merged_df[self.merged_df[self.config["result_column"]].isin(['NG', 'BK'])]
        
    def _create_pivot_table(self, filtered_df):
        pivot_count = filtered_df.pivot_table(
            index=self.config["bug_no_column"],
            values=self.config["test_id_column"],
            aggfunc='count'
        ).reset_index().rename(columns={self.config["test_id_column"]: '件数'})
        
        pivot_test_names = filtered_df.groupby(self.config["bug_no_column"])[self.config["test_name_column"]] \
            .agg(lambda x: ', '.join(sorted(set(x.dropna().astype(str))))) \
            .reset_index(name='_temp_test_names')
        
        pivot_test_names = pivot_test_names.rename(columns={'_temp_test_names': self.config["test_name_column"]})
        
        return pd.merge(pivot_count, pivot_test_names, on=self.config["bug_no_column"], how='left')
        
    def _load_external_data(self):
        # 내부 버그리스트가 이미 로드되어 있으면 그것을 사용
        if self.bug_data is not None:
            return self.bug_data[self.config["bug_file_columns"]]
            
        # 없으면 파일에서 로드
        bug_list_path = self._find_external_file(self.config["bug_file_name"])
        if bug_list_path is None:
            st.error(f"{self.config['bug_file_name']} ファイルが見つかりません。")
            return None
            
        try:
            bug_list_df = pd.read_excel(bug_list_path, sheet_name="一覧", engine='openpyxl')
            return bug_list_df[self.config["bug_file_columns"]]
        except Exception as e:
            st.error(f"{self.config['bug_file_name']} ファイルロード失敗: {e}")
            return None
            
    def _merge_data(self, pivot_df, external_data):
        # 1. external_data 유효성 검사 및 준비
        if external_data is None:
            # external_data가 없으면 pivot_df를 반환하되, 예상 컬럼 구조 맞추기
            final_cols = [self.config["bug_no_column"], "件数", self.config["test_name_column"]]
            for col in final_cols:
                if col not in pivot_df.columns:
                    pivot_df[col] = 0 if col == "件数" else (None if col == self.config["bug_no_column"] else "")
            # bug_file_columns는 없으므로 추가하지 않음
            return pivot_df[final_cols].copy()

        # external_data의 'No' 컬럼 정리
        external_data = external_data.rename(columns={col: col.strip() for col in external_data.columns})
        if 'No' not in external_data.columns:
            st.error(f"{self.config['bug_file_name']} に 'No' カラムが見つかりません。")
            # 'No' 컬럼이 없으면 병합 불가, 빈 데이터프레임 반환
            return pd.DataFrame(columns=[self.config["bug_no_column"]] + self.config["bug_file_columns"] + ["件数", self.config["test_name_column"]])

        external_data['No_original'] = external_data['No'] # 원본 No 유지
        external_data['No'] = pd.to_numeric(external_data['No'], errors='coerce')
        external_data = external_data.dropna(subset=['No'])
        if not external_data.empty:
             external_data['No'] = external_data['No'].astype(int)

        if external_data.empty:
            # 유효한 external_data가 없으면 빈 DataFrame 반환
            final_columns = [self.config["bug_no_column"]] + [col for col in self.config["bug_file_columns"] if col != 'No'] + ["件数", self.config["test_name_column"]]
            return pd.DataFrame(columns=final_columns)

        # 2. pivot_df 준비 (BugNumber 추출)
        if not pivot_df.empty:
            def extract_bug_number(bug_db_no):
                if pd.isna(bug_db_no):
                    return None
                match = re.search(self.config["bug_regex"], str(bug_db_no))
                return int(match.group(1)) if match else None

            pivot_df['BugNumber'] = pivot_df[self.config["bug_no_column"]].apply(extract_bug_number)
            pivot_df = pivot_df.dropna(subset=['BugNumber'])
            if not pivot_df.empty:
                pivot_df['BugNumber'] = pivot_df['BugNumber'].astype(int)
        else:
            # pivot_df가 처음부터 비어있으면 필요한 컬럼 추가
            pivot_df = pd.DataFrame(columns=[self.config["bug_no_column"], '件数', self.config["test_name_column"], 'BugNumber'])


        # 3. Merge 수행 (external_data 기준 right merge)
        # pivot_df가 비어있어도 external_data 기준으로 병합됨
        merged_result = pd.merge(
            pivot_df,
            external_data,
            left_on='BugNumber', right_on='No',
            how='right',
            suffixes=('_pivot', '_external') # 충돌 시 컬럼명 구분
        )

        # 4. 컬럼 정리 및 값 채우기
        # '件数' 컬럼 처리
        count_col = '件数_pivot' if '件数_pivot' in merged_result.columns else '件数'
        if count_col in merged_result.columns:
            merged_result['件数'] = merged_result[count_col].fillna(0).astype(int)
        else:
            merged_result['件数'] = 0

        # 'test_name_column' 처리
        test_name_col_config = self.config["test_name_column"]
        test_name_col_pivot = test_name_col_config + '_pivot'
        if test_name_col_pivot in merged_result.columns:
            merged_result[test_name_col_config] = merged_result[test_name_col_pivot].fillna('')
        elif test_name_col_config in merged_result.columns: # pivot_df가 비어있을 때 external_data에 같은 이름 컬럼 있으면 유지될수도?
             merged_result[test_name_col_config] = merged_result[test_name_col_config].fillna('')
        else:
            merged_result[test_name_col_config] = ''

        # 'bug_no_column' 생성 (external_data의 원본 No 기준)
        # merge 후 external 데이터의 No는 'No' 또는 'No_external' 일 수 있음
        # 여기서는 external_data에서 미리 복사해둔 'No_original' 사용
        no_original_col = 'No_original_external' if 'No_original_external' in merged_result.columns else 'No_original'
        merged_result[self.config["bug_no_column"]] = merged_result[no_original_col].apply(
             lambda no: self.config["bug_pattern_template"].replace("{Int}", str(no)) if pd.notna(no) else None
        )

        # 5. 최종 컬럼 선택 및 순서 지정
        # 원하는 최종 컬럼 순서 정의
        desired_order = [
            self.config["bug_no_column"], 
            "JIRA#", 
            "件数", 
            "概要", 
            self.config["test_name_column"], 
            "ステータス"
        ]

        # merge 결과에 존재하는 컬럼 이름 확인 (suffix 고려)
        final_cols_mapping = {}
        for col_name in desired_order:
            col_suffixed_pivot = col_name + '_pivot'
            col_suffixed_external = col_name + '_external'
            
            if col_name in merged_result.columns:
                final_cols_mapping[col_name] = col_name
            elif col_suffixed_pivot in merged_result.columns: # pivot에서 온 컬럼 (件数, test_name_column 등)
                 final_cols_mapping[col_name] = col_suffixed_pivot
            elif col_suffixed_external in merged_result.columns: # external_data에서 온 컬럼
                 final_cols_mapping[col_name] = col_suffixed_external
            # bug_no_column은 merge 후 직접 생성했으므로 suffix 없음
            elif col_name == self.config["bug_no_column"] and col_name in merged_result.columns:
                 final_cols_mapping[col_name] = col_name

        # 원하는 순서대로 실제 존재하는 컬럼 리스트 생성
        final_cols_existing_suffixed = [final_cols_mapping[col] for col in desired_order if col in final_cols_mapping]
        
        # 존재하는 컬럼만 선택하고 복사
        merged_result = merged_result[final_cols_existing_suffixed].copy()

        # 컬럼 이름에서 suffix 제거
        merged_result.columns = [col.replace('_pivot', '').replace('_external', '') for col in merged_result.columns]

        # 최종 순서 확인 (디버깅용, 필요시 주석 해제)
        # print("Final Bug Table Columns:", merged_result.columns.tolist())
        
        # 건수가 0인 행 제외
        merged_result = merged_result[merged_result['件数'] > 0]
        
        return merged_result

class QATableCreator(TableCreator):
    def __init__(self, config, merged_df, find_external_file):
        super().__init__(config, merged_df, find_external_file)
        self.qa_data = None  # 내부 QA리스트 데이터

    def _filter_data(self):
        return self.merged_df[self.merged_df[self.config["result_column"]].isin(['QA'])]
        
    def _create_pivot_table(self, filtered_df):
        pivot_count = filtered_df.pivot_table(
            index=self.config["qa_no_column"],
            values=self.config["test_id_column"],
            aggfunc='count'
        ).reset_index().rename(columns={self.config["test_id_column"]: '件数'})
        
        # groupby().apply() 대신 groupby().agg() 사용 및 reset_index 이름 충돌 방지
        pivot_test_names = filtered_df.groupby(self.config["qa_no_column"])[self.config["test_name_column"]] \
            .agg(lambda x: ', '.join(sorted(set(x.dropna().astype(str))))) \
            .reset_index(name='_temp_test_names') # 임시 이름 지정
        
        # 임시 이름 -> 원래 컬럼 이름으로 변경
        pivot_test_names = pivot_test_names.rename(columns={'_temp_test_names': self.config["test_name_column"]})
        
        return pd.merge(pivot_count, pivot_test_names, on=self.config["qa_no_column"], how='left')
        
    def _load_external_data(self):
        # 내부 QA리스트가 이미 로드되어 있으면 그것을 사용
        if self.qa_data is not None:
            return self.qa_data[self.config["qa_file_columns"]]
            
        # 없으면 파일에서 로드
        qa_list_path = self._find_external_file(self.config["qa_file_name"])
        if qa_list_path is None:
            st.error(f"{self.config['qa_file_name']} ファイルが見つかりません")
            return None
            
        try:
            qa_list_df = pd.read_excel(qa_list_path, sheet_name="一覧", engine='openpyxl')
            return qa_list_df[self.config["qa_file_columns"]]
        except Exception as e:
            st.error(f"{self.config['qa_file_name']} ファイルロード失敗: {e}")
            return None
            
    def _merge_data(self, pivot_df, external_data):
        # 1. external_data 유효성 검사 및 준비
        if external_data is None:
            # external_data가 없으면 pivot_df를 반환하되, 예상 컬럼 구조 맞추기
            final_cols = [self.config["qa_no_column"], "件数", self.config["test_name_column"]]
            for col in final_cols:
                if col not in pivot_df.columns:
                    pivot_df[col] = 0 if col == "件数" else (None if col == self.config["qa_no_column"] else "")
            # qa_file_columns는 없으므로 추가하지 않음
            return pivot_df[final_cols].copy()

        # external_data의 'No' 컬럼 정리
        external_data = external_data.rename(columns={col: col.strip() for col in external_data.columns})
        if 'No' not in external_data.columns:
            st.error(f"{self.config['qa_file_name']} に 'No' カラムが見つかりません。")
            return pd.DataFrame(columns=[self.config["qa_no_column"]] + self.config["qa_file_columns"] + ["件数", self.config["test_name_column"]])

        external_data['No_original'] = external_data['No'] # 원본 No 유지
        external_data['No'] = pd.to_numeric(external_data['No'], errors='coerce')
        external_data = external_data.dropna(subset=['No'])
        if not external_data.empty:
             external_data['No'] = external_data['No'].astype(int)

        if external_data.empty:
            # 유효한 external_data가 없으면 빈 DataFrame 반환
            final_columns = [self.config["qa_no_column"]] + [col for col in self.config["qa_file_columns"] if col != 'No'] + ["件数", self.config["test_name_column"]]
            return pd.DataFrame(columns=final_columns)

        # 2. pivot_df 준비 (QANumber 추출)
        if not pivot_df.empty:
            def extract_qa_number(qa_db_no):
                if pd.isna(qa_db_no):
                    return None
                match = re.search(self.config["qa_regex"], str(qa_db_no))
                return int(match.group(1)) if match else None

            pivot_df['QANumber'] = pivot_df[self.config["qa_no_column"]].apply(extract_qa_number)
            pivot_df = pivot_df.dropna(subset=['QANumber'])
            if not pivot_df.empty:
                pivot_df['QANumber'] = pivot_df['QANumber'].astype(int)
        else:
            # pivot_df가 처음부터 비어있으면 필요한 컬럼 추가
            pivot_df = pd.DataFrame(columns=[self.config["qa_no_column"], '件数', self.config["test_name_column"], 'QANumber'])

        # 3. Merge 수행 (pivot_df 기준 left merge)
        # QA는 pivot_df(시험 결과에 있는 QA 항목) 기준으로 병합
        merged_result = pd.merge(
            pivot_df,
            external_data,
            left_on='QANumber', right_on='No',
            how='left', # pivot_df 기준 병합
            suffixes=('_pivot', '_external')
        )

        # 4. 컬럼 정리 및 값 채우기
        # '件数' 컬럼 처리 (pivot_df에 항상 있어야 함)
        count_col = '件数_pivot' if '件数_pivot' in merged_result.columns else '件数'
        if count_col in merged_result.columns:
            merged_result['件数'] = merged_result[count_col].fillna(0).astype(int)
            # pivot에서 온 件数 컬럼은 이름 변경 없이 유지 (rename에서 이미 件数로 바뀜)
        else:
            # Left merge 이므로 pivot_df가 비어있지 않다면 件数는 있어야 함. 비어있으면 merged_result도 비어있음.
            merged_result['件数'] = 0 # merged_result가 비어있지 않는데 件数 컬럼이 없는 예외 케이스 대비

        # 'test_name_column' 처리 (pivot_df에 있어야 함)
        test_name_col_config = self.config["test_name_column"]
        test_name_col_pivot = test_name_col_config + '_pivot'
        if test_name_col_pivot in merged_result.columns:
            merged_result[test_name_col_config] = merged_result[test_name_col_pivot].fillna('')
        elif test_name_col_config not in merged_result.columns:
             merged_result[test_name_col_config] = '' # 컬럼 자체가 없는 경우 생성
        else: # suffix 없이 존재하는 경우
             merged_result[test_name_col_config] = merged_result[test_name_col_config].fillna('')

        # 'qa_no_column' 처리 (pivot_df에 있어야 함)
        # pivot_df에서 온 qa_no_column을 그대로 사용. merge 시 이름 충돌 없었으면 _pivot 안붙음
        qa_no_col_config = self.config["qa_no_column"]
        qa_no_col_pivot = qa_no_col_config + '_pivot'
        if qa_no_col_pivot in merged_result.columns:
             merged_result[qa_no_col_config] = merged_result[qa_no_col_pivot]
        elif qa_no_col_config not in merged_result.columns and not merged_result.empty:
             # QANumber와 external No로 다시 생성 시도 (비추천)
             # 여기서는 pivot_df에 qa_no_column이 있다고 가정
             st.warning(f"QA Merge 결과에서 {qa_no_col_config} 컬럼을 찾을 수 없습니다.")
             merged_result[qa_no_col_config] = None

        # 5. 최종 컬럼 선택 및 순서 지정
        # 원하는 최종 컬럼 순서 정의
        desired_order = [
            self.config["qa_no_column"], 
            "件数", 
            "質問者", 
            "コメント", 
            "回答", 
            self.config["test_name_column"], 
            "ステータス"
        ]

        # merge 결과에 존재하는 컬럼 이름 확인 (suffix 고려)
        final_cols_mapping = {}
        for col_name in desired_order:
            col_suffixed_pivot = col_name + '_pivot'
            col_suffixed_external = col_name + '_external'
            
            if col_name in merged_result.columns: # suffix 없이 존재 (qa_no_column 등)
                final_cols_mapping[col_name] = col_name
            elif col_suffixed_pivot in merged_result.columns: # pivot에서 온 컬럼 (件数, test_name_column 등)
                 final_cols_mapping[col_name] = col_suffixed_pivot
            elif col_suffixed_external in merged_result.columns: # external_data에서 온 컬럼
                 final_cols_mapping[col_name] = col_suffixed_external
            # qa_no_column은 pivot에서 왔을 가능성
            elif col_name == self.config["qa_no_column"] and col_suffixed_pivot in merged_result.columns:
                 final_cols_mapping[col_name] = col_suffixed_pivot

        # 원하는 순서대로 실제 존재하는 컬럼 리스트 생성
        final_cols_existing_suffixed = [final_cols_mapping[col] for col in desired_order if col in final_cols_mapping]
        
        # 존재하는 컬럼만 선택하고 복사
        merged_result = merged_result[final_cols_existing_suffixed].copy()

        # 컬럼 이름에서 suffix 제거
        merged_result.columns = [col.replace('_pivot', '').replace('_external', '') for col in merged_result.columns]

        # 최종 순서 확인 (디버깅용, 필요시 주석 해제)
        # print("Final QA Table Columns:", merged_result.columns.tolist())
        
        # 건수가 0인 행 제외
        merged_result = merged_result[merged_result['件数'] > 0]
        
        return merged_result 