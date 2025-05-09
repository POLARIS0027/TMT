import os
import re
import pandas as pd
from datetime import datetime
import streamlit as st
from table_creator import BugTableCreator, QATableCreator
from dataclasses import dataclass
from typing import Protocol
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='[%(asctime)s]: %(levelname)s - %(filename)s\n Line:%(lineno)d: %(message)s')
logger = logging.getLogger(__name__)

class OKCalculator(Protocol):
    """OK 계산 전략 인터페이스"""
    def calculate(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        """데이터프레임을 받아 계산된 결과를 반환"""
        pass

class BaseOKCalculator:
    """기본 OK 계산 클래스"""
    def _prepare_data(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        """공통 데이터 전처리"""
        if df.empty:
            return pd.DataFrame()
        df = df.copy()
        return df

class CumulativeOKCalculator(BaseOKCalculator, OKCalculator):
    """누적 OK 계산 전략"""
    def calculate(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        df = self._prepare_data(df, config)
        if df.empty:
            return df
        df['OK_cumulative'] = df['OK'].cumsum()
        return df[[config["date_column"], 'OK_cumulative']]

class DailyOKCalculator(BaseOKCalculator, OKCalculator):
    """일별 OK 계산 전략"""
    def calculate(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        df = self._prepare_data(df, config)
        if df.empty:
            return df
        return df[[config["date_column"], 'OK']]

@dataclass
class TestResult:
    """테스트 결과를 담는 데이터 클래스"""
    summary_df: pd.DataFrame
    merged_df: pd.DataFrame
    bug_table: pd.DataFrame
    qa_table: pd.DataFrame
    ok_table: pd.DataFrame
    cumulative_ok_df: pd.DataFrame
    daily_ok_df: pd.DataFrame

class DataCollector:
    def __init__(self, selected_folder_path, config, bug_list_folder=None, qa_list_folder=None):
        self.config = config
        self.selected_folder_path = selected_folder_path
        # bug_list_folder와 qa_list_folder가 지정되지 않으면 selected_folder_path 사용
        self.bug_list_folder = bug_list_folder if bug_list_folder else selected_folder_path
        self.qa_list_folder = qa_list_folder if qa_list_folder else selected_folder_path
        # 가능한 시험 결과 리스트
        self.categories = ['OK', 'NG', 'BK', 'NY', 'TS', 'QA', 'NT'] 
        # 수집된 시험데이터와 요약 저장용
        self.results = []
        self.summaries = []
        self.merged_df = pd.DataFrame()  # "統合" 시트에 대한 병합 DataFrame
        # 에러 및 경고 메시지 저장용
        self.invalid_results = []  # 부적절한 시험 결과
        self.qa_without_no = []    # QA 번호 누락
        self.bug_without_no = []   # 버그 번호 누락

    def collect_data(self) -> TestResult:
        """데이터 수집 및 처리 파이프라인 실행"""
        # 폴더 경로 유효성 검사
        if not self.selected_folder_path or not os.path.exists(self.selected_folder_path):
            logger.error("フォルダーが選択されていないか、無効なパスです。")
            # UI에는 간결한 메시지 또는 상태 표시
            st.error("선택된 폴더가 유효하지 않습니다. CLI 로그를 확인하세요.")
            return TestResult(
                summary_df=pd.DataFrame(),
                merged_df=pd.DataFrame(),
                bug_table=pd.DataFrame(),
                qa_table=pd.DataFrame(),
                ok_table=pd.DataFrame(),
                cumulative_ok_df=pd.DataFrame(),
                daily_ok_df=pd.DataFrame()
            )
            
        # 1. 데이터 수집
        excel_files = self._get_excel_files()
        
        # 엑셀 파일이 없는 경우 에러 메시지 표시
        if not excel_files:
            logger.error("指定されたフォルダーにExcelファイルが見つかりません。")
            st.error("지정된 폴더에 Excel 파일이 없습니다. CLI 로그를 확인하세요.")
            return TestResult(
                summary_df=pd.DataFrame(),
                merged_df=pd.DataFrame(),
                bug_table=pd.DataFrame(),
                qa_table=pd.DataFrame(),
                ok_table=pd.DataFrame(),
                cumulative_ok_df=pd.DataFrame(),
                daily_ok_df=pd.DataFrame()
            )
            
        merged_data = self._collect_excel_data(excel_files)
        
        # 2. 데이터 병합
        self.merged_df = self._merge_data(merged_data)
        
        # 3. 데이터 처리
        return self._process_data()

    def _collect_excel_data(self, excel_files):
        """엑셀 파일에서 데이터 수집"""
        test_data = []  # 시험표 데이터
        bug_data = None  # 내부 버그리스트
        qa_data = None  # 내부 QA리스트
        success_count = 0
        
        for file_path in excel_files:
            try:
                file_name = os.path.basename(file_path)
                df = self._read_and_preprocess_excel(file_path)
                if df is None:
                    continue
                
                # 내부 버그리스트와 QA리스트는 별도로 저장
                if file_name == self.config["bug_file_name"]:
                    bug_data = df
                    success_count += 1
                    logger.info(f"{file_name} の読み込みが完了しました。")
                    continue
                elif file_name == self.config["qa_file_name"]:
                    qa_data = df
                    success_count += 1
                    logger.info(f"{file_name} の読み込みが完了しました。")
                    continue
                
                # 시험표 데이터 처리
                test_data.append(df)
                counts = self._count_test_results(df)
                counts['file_name'] = file_name
                self.summaries.append(counts)
                
                success_count += 1
                logger.info(f"{file_name} の読み込みが完了しました。")
            except Exception as e:
                logger.error(f"{os.path.basename(file_path)} の読み込み中にエラーが発生しました: {str(e)}")
                
        if success_count == 0:
            logger.error("有効なExcelファイルが見つかりませんでした。")
            st.error("유효한 Excel 파일을 찾지 못했습니다. CLI 로그를 확인하세요.")
            
        # 시험표 데이터만 병합하여 반환
        self.bug_data = bug_data
        self.qa_data = qa_data
        return test_data

    def _merge_data(self, merged_data):
        """수집된 데이터 병합"""
        if merged_data:
            return pd.concat(merged_data, ignore_index=True)
        return pd.DataFrame()

    def _process_data(self) -> TestResult:
        """수집된 데이터 처리"""
        summary_df = self._create_summary_dataframe()
        bug_table = self._create_bug_table()
        qa_table = self._create_qa_table()
        ok_table = self._create_ok_table()
        cumulative_ok_df = self._compute_cumulative_ok(ok_table)
        daily_ok_df = self._compute_daily_ok(ok_table)

        # 문제가 있는 항목들을 데이터프레임으로 표시
        if self.invalid_results:
            logger.warning("不正な試験結果一覧：")
            invalid_df = pd.DataFrame(self.invalid_results)
            invalid_df.columns = ['ファイル名', 'テストID', '結果']
            logger.warning(f"부적절한 시험 결과:\n{invalid_df.to_string()}")
            # UI에는 요약 정보 또는 알림만 표시
            st.warning(f"{len(self.invalid_results)}건의 부적절한 시험 결과가 있습니다. CLI 로그를 확인하세요.")

        if self.qa_without_no:
            logger.warning("QA番号未入力項目一覧：")
            qa_df = pd.DataFrame(self.qa_without_no)
            qa_df.columns = ['ファイル名', 'テストID']
            logger.warning(f"QA 번호 미입력 항목:\n{qa_df.to_string()}")
            st.warning(f"{len(self.qa_without_no)}건의 QA 번호 미입력 항목이 있습니다. CLI 로그를 확인하세요.")

        if self.bug_without_no:
            logger.warning("バグ番号未入力項目一覧：")
            bug_df = pd.DataFrame(self.bug_without_no)
            bug_df.columns = ['ファイル名', 'テストID']
            logger.warning(f"버그 번호 미입력 항목:\n{bug_df.to_string()}")
            st.warning(f"{len(self.bug_without_no)}건의 버그 번호 미입력 항목이 있습니다. CLI 로그를 확인하세요.")

        return TestResult(
            summary_df=summary_df,
            merged_df=self.merged_df,
            bug_table=bug_table,
            qa_table=qa_table,
            ok_table=ok_table,
            cumulative_ok_df=cumulative_ok_df,
            daily_ok_df=daily_ok_df
        )

    def _read_and_preprocess_excel(self, file_path):
        """
        엑셀 파일 읽기 및 전처리.
        파일 종류(시험표, 버그/QA 목록)에 따라 다른 전처리 수행.
        - 필수 컬럼 존재 확인
        - 데이터 타입 변환 (날짜, 숫자)
        - NaN 값 처리
        - 외부 목록의 경우 원본 'No' 값 보존
        정제된 DataFrame 또는 처리 불가 시 None 반환.
        """
        try:
            config = self.config
            excel_file = pd.ExcelFile(file_path)
            file_name = os.path.basename(file_path)
            is_external_list = file_name in [config["bug_file_name"], config["qa_file_name"]]
            sheet_name = "一覧" if is_external_list else config["sheet_name"]

            # 1. 시트 존재 확인
            if sheet_name not in excel_file.sheet_names:
                logger.warning(f"'{file_name}'に'{sheet_name}'シートが存在しません。")
                return None

            # 2. 데이터 로드 및 컬럼 공백 제거
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=0, engine='openpyxl')
            df.columns = df.columns.str.strip()

            # 3. 필수 컬럼 존재 확인
            required_columns = []
            if is_external_list:
                # 외부 목록 (버그/QA) 필수 컬럼
                list_type = "bug" if file_name == config["bug_file_name"] else "qa"
                # config 키 존재 여부 확인 추가
                external_cols_key = f"{list_type}_file_columns"
                if external_cols_key in config:
                    required_columns = ['No'] + config[external_cols_key]
                else:
                    logger.error(f"Config 파일에 '{external_cols_key}' 키가 없습니다.")
                    return None
            else:
                # 시험표 필수 컬럼 (config 키 존재 여부 확인)
                test_id_col = config.get("test_id_column")
                result_col = config.get("result_column")
                date_col = config.get("date_column")
                bug_no_col = config.get("bug_no_column")
                qa_no_col = config.get("qa_no_column")
                test_name_col = config.get("test_name_column") # 시험명은 필수는 아님
                
                required_columns = [col for col in [test_id_col, result_col, date_col, bug_no_col, qa_no_col] if col] # None 제외
                
                if not test_name_col or test_name_col not in df.columns:
                     logger.warning(f"'{file_name}'に'{test_name_col or 'test_name_column 설정값'}'列がありません。試験名なしで処理を続行します。")
                     # 시험명 컬럼이 없거나 config에 설정 안됐으면 빈 컬럼 추가
                     df[test_name_col if test_name_col else '시험명_임시'] = '' 
                     # 임시 이름 사용 시 config에도 반영해야 할 수 있으나, 여기서는 일단 추가만 함
                     # 또는 test_name_col을 None으로 두고 후처리에서 처리
                elif test_name_col: # 시험명 컬럼이 존재하면 required_columns에 추가하지 않아도 됨
                    pass

            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                logger.error(f"'{file_name}' ({sheet_name}シート)に必要なカラムがありません: {', '.join(missing_cols)}")
                return None

            # 4. 데이터 타입 변환 및 NaN 처리
            if is_external_list:
                # 외부 목록 처리
                df['No_original'] = df['No'] # 원본 'No' 값 보존
                df['No'] = pd.to_numeric(df['No'], errors='coerce') # 숫자 변환 시도
                initial_rows = len(df)
                df = df.dropna(subset=['No']) # 숫자 변환 실패(NaN) 행 제거
                if len(df) < initial_rows:
                     logger.warning(f"'{file_name}'의 'No'カラムに数値でない、または空の値が含まれる行を削除しました。")
                if not df.empty:
                     df['No'] = df['No'].astype(int) # 정수형으로 변환
            else:
                # 시험표 처리
                date_col = config["date_column"] # 이미 존재 확인됨
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce') # 날짜 변환 시도
                initial_rows = len(df)
                df = df.dropna(subset=[date_col]) # 날짜 변환 실패(NaT) 행 제거
                if len(df) < initial_rows:
                    logger.warning(f"'{file_name}'의 '{date_col}'カラムに日付でない、または空の値が含まれる行を削除しました。")

                # 시험 결과 유효성 검사 (기존 로직 유지, result_col 사용)
                result_col = config["result_column"]
                invalid_results = df[~df[result_col].isin(self.categories) & df[result_col].notna()]
                if not invalid_results.empty:
                    test_id_col = config["test_id_column"]
                    for idx, row in invalid_results.iterrows():
                        self.invalid_results.append({
                            'file_name': file_name,
                            'test_id': row[test_id_col],
                            'result': row[result_col]
                        })
                    st.warning(f"'{file_name}'に不正な試験結果({invalid_results[result_col].unique()})が含まれています。CLI 로그에 상세 정보가 기록됩니다.") # UI 메시지 변경
                    logger.warning(f"'{file_name}'에 포함된 부적절한 시험 결과: {invalid_results[[config['test_id_column'], result_col]].to_dict('records')}")

                # QA/Bug 번호 누락 검사 (기존 로직 유지, 각 컬럼 사용)
                qa_no_col = config["qa_no_column"]
                test_id_col = config["test_id_column"]
                qa_without_no = df[
                    (df[result_col] == 'QA') &
                    (df[qa_no_col].isna() | (df[qa_no_col] == ''))
                ]
                if not qa_without_no.empty:
                    for idx, row in qa_without_no.iterrows():
                        self.qa_without_no.append({
                            'file_name': file_name,
                            'test_id': row[test_id_col]
                        })
                    st.warning(f"'{file_name}'에 QA 번호가 누락된 항목이 있습니다. CLI 로그에 상세 정보가 기록됩니다.") # UI 메시지 변경
                    logger.warning(f"'{file_name}'에 QA 번호 누락: {qa_without_no[[config['test_id_column']]].to_dict('records')}")

                bug_no_col = config["bug_no_column"]
                bug_without_no = df[
                    (df[result_col].isin(['NG', 'BK'])) &
                    (df[bug_no_col].isna() | (df[bug_no_col] == ''))
                ]
                if not bug_without_no.empty:
                    for idx, row in bug_without_no.iterrows():
                        self.bug_without_no.append({
                            'file_name': file_name,
                            'test_id': row[test_id_col]
                        })
                    st.warning(f"'{file_name}'에 버그 번호가 누락된 항목이 있습니다. CLI 로그에 상세 정보가 기록됩니다.") # UI 메시지 변경
                    logger.warning(f"'{file_name}'에 버그 번호 누락: {bug_without_no[[config['test_id_column']]].to_dict('records')}")

            # 5. 정제된 데이터프레임 반환
            return df

        except Exception as e:
            logger.error(f"'{os.path.basename(file_path)}' ({sheet_name}シート) の読み込み・前処理中にエラーが発生しました: {str(e)}")
            return None

    # '試験結果' 컬럼의 값을 config["result_column"]로 처리하여 카테고리별 개수를 계산
    def _count_test_results(self, df):
        result_counts = df[self.config["result_column"]].value_counts()
        counts = {category: result_counts.get(category, 0) for category in self.categories}
        return counts

    # 수집된 데이터를 기반으로 요약 dataframe 생성 (총 항목 수, 진행률 포함)
    def _create_summary_dataframe(self):
        summary_df = pd.DataFrame(self.summaries)
        current_date = datetime.now().strftime('%Y/%m/%d')
        total_counts = summary_df[self.categories].sum()
        total_counts['file_name'] = current_date

        summary_df = pd.concat([summary_df, pd.DataFrame([total_counts])], ignore_index=True)
        desired_order = ['file_name'] + self.categories
        summary_df = summary_df[desired_order]
        summary_df['総項目数'] = summary_df[self.categories].sum(axis=1)

        denom = (summary_df['総項目数'] - summary_df['NT']).replace(0, float('nan'))
        summary_df['進捗率(%)'] = (summary_df['OK'] / denom) * 100
        summary_df['進捗率(%)'] = summary_df['進捗率(%)'].fillna(0).round(1)

        return summary_df

    # 특정 파일(버그, QA 리스트)을 지정된 폴더에서 검색하여 경로 반환 (config 활용)
    def _find_external_file(self, target_file):
        if target_file == self.config["bug_file_name"]:
            search_folder = self.bug_list_folder
        elif target_file == self.config["qa_file_name"]:
            search_folder = self.qa_list_folder
        else:
            search_folder = self.selected_folder_path

        for root, _, files in os.walk(search_folder):
            for file in files:
                if file == target_file:
                    return os.path.join(root, file)
        return None

    def _create_bug_table(self):
        """버그 테이블 생성"""
        # 시험표에서 NG, BK인 항목만 필터링
        filtered_df = self.merged_df[self.merged_df[self.config["result_column"]].isin(['NG', 'BK'])]
        creator = BugTableCreator(self.config, filtered_df, self._find_external_file)
        creator.bug_data = self.bug_data  # 내부 버그리스트 데이터 전달
        return creator.create_table()

    def _create_qa_table(self):
        """QA 테이블 생성"""
        # 시험표에서 QA인 항목만 필터링
        filtered_df = self.merged_df[self.merged_df[self.config["result_column"]] == 'QA']
        creator = QATableCreator(self.config, filtered_df, self._find_external_file)
        creator.qa_data = self.qa_data  # 내부 QA리스트 데이터 전달
        return creator.create_table()

    def _create_ok_table(self):
        """
        'OK' 결과를 날짜별로 집계한 테이블 생성.
        입력 merged_df는 이미 전처리되었다고 가정 (날짜 컬럼 유효, NaT 없음).
        """
        config = self.config
        date_col = config["date_column"]
        result_col = config["result_column"]
        test_id_col = config["test_id_column"]
        final_cols = [date_col, 'OK'] # 최종 반환할 컬럼

        # 입력 데이터프레임 및 필수 컬럼 존재 확인
        # date_col은 전처리 단계에서 확인됨
        if self.merged_df.empty or result_col not in self.merged_df.columns or test_id_col not in self.merged_df.columns:
            # 필수 컬럼 없으면 집계 불가
            if result_col not in self.merged_df.columns: logger.error(f"OK 테이블 생성 불가: '{result_col}' 컬럼이 없습니다.")
            if test_id_col not in self.merged_df.columns: logger.error(f"OK 테이블 생성 불가: '{test_id_col}' 컬럼이 없습니다.")
            return pd.DataFrame(columns=final_cols)

        # pivot_table 생성 (오류 가능성 낮음)
        try:
            pivot_table = self.merged_df.pivot_table(
                index=date_col,
                columns=result_col,
                values=test_id_col,
                aggfunc='count',
                fill_value=0
            )
        except Exception as e: # 예상치 못한 오류 처리
             logger.error(f"OK テーブル作成中に予期せぬエラーが発生しました: {e}")
             return pd.DataFrame(columns=final_cols)

        # 'OK' 컬럼이 없는 경우 처리
        if 'OK' not in pivot_table.columns:
            pivot_table['OK'] = 0

        # 필요한 컬럼('OK')만 선택하고 인덱스(날짜)를 컬럼으로 변환
        ok_df = pivot_table[['OK']].reset_index()

        return ok_df

    def _compute_ok(self, ok_table: pd.DataFrame, calculator: OKCalculator) -> pd.DataFrame:
        """OK 계산을 수행하는 메서드"""
        return calculator.calculate(ok_table, self.config)

    def _compute_cumulative_ok(self, ok_table: pd.DataFrame) -> pd.DataFrame:
        """누적 OK 테이블 계산"""
        return self._compute_ok(ok_table, CumulativeOKCalculator())

    def _compute_daily_ok(self, ok_table: pd.DataFrame) -> pd.DataFrame:
        """일별 OK 테이블 계산"""
        return self._compute_ok(ok_table, DailyOKCalculator())

    # 지정된 폴더에서 .xlsx 파일을 검색하여 리스트로 반환
    def _get_excel_files(self):
        excel_files = []
        for root, _, files in os.walk(self.selected_folder_path):
            for file in files:
                if file.endswith(".xlsx"):
                    excel_files.append(os.path.join(root, file))
        return excel_files
