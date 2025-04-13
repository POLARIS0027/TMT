import os
import re
import pandas as pd
from datetime import datetime
import streamlit as st
from table_creator import BugTableCreator, QATableCreator
from dataclasses import dataclass
from typing import Protocol

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
            st.error("フォルダーが選択されていないか、無効なパスです。")
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
            st.error("指定されたフォルダーにExcelファイルが見つかりません。")
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
                    st.success(f"{file_name} の読み込みが完了しました。")
                    continue
                elif file_name == self.config["qa_file_name"]:
                    qa_data = df
                    success_count += 1
                    st.success(f"{file_name} の読み込みが完了しました。")
                    continue
                
                # 시험표 데이터 처리
                test_data.append(df)
                counts = self._count_test_results(df)
                counts['file_name'] = file_name
                self.summaries.append(counts)
                
                success_count += 1
                st.success(f"{file_name} の読み込みが完了しました。")
            except Exception as e:
                st.error(f"{os.path.basename(file_path)} の読み込み中にエラーが発生しました: {str(e)}")
                
        if success_count == 0:
            st.error("有効なExcelファイルが見つかりませんでした。")
            
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
            st.error("不正な試験結果一覧：")
            invalid_df = pd.DataFrame(self.invalid_results)
            invalid_df.columns = ['ファイル名', 'テストID', '結果']
            st.dataframe(
                invalid_df,
                column_config={
                    'ファイル名': st.column_config.TextColumn('ファイル名', width='medium'),
                    'テストID': st.column_config.TextColumn('テストID', width='medium'),
                    '結果': st.column_config.TextColumn('結果', width='small'),
                },
                hide_index=True
            )

        if self.qa_without_no:
            st.warning("QA番号未入力項目一覧：")
            qa_df = pd.DataFrame(self.qa_without_no)
            qa_df.columns = ['ファイル名', 'テストID']
            st.dataframe(
                qa_df,
                column_config={
                    'ファイル名': st.column_config.TextColumn('ファイル名', width='medium'),
                    'テストID': st.column_config.TextColumn('テストID', width='medium'),
                },
                hide_index=True
            )

        if self.bug_without_no:
            st.warning("バグ番号未入力項目一覧：")
            bug_df = pd.DataFrame(self.bug_without_no)
            bug_df.columns = ['ファイル名', 'テストID']
            st.dataframe(
                bug_df,
                column_config={
                    'ファイル名': st.column_config.TextColumn('ファイル名', width='medium'),
                    'テストID': st.column_config.TextColumn('テストID', width='medium'),
                },
                hide_index=True
            )

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
        """엑셀 파일 읽기 및 전처리"""
        try:
            config = self.config
            excel_file = pd.ExcelFile(file_path)
            file_name = os.path.basename(file_path)
            
            # 내부 버그리스트와 QA리스트는 "一覧" 시트를 읽음
            if file_name in [config["bug_file_name"], config["qa_file_name"]]:
                if "一覧" not in excel_file.sheet_names:
                    st.warning(f"'{file_name}'に'一覧'シートが存在しません。")
                    return None
                return pd.read_excel(file_path, sheet_name="一覧", header=0, engine='openpyxl')
            
            # 시험표 파일 처리
            if config["sheet_name"] not in excel_file.sheet_names:
                st.warning(f"'{file_name}'に'{config['sheet_name']}'シートが存在しません。")
                return None

            df = pd.read_excel(file_path, sheet_name=config["sheet_name"], header=0, engine='openpyxl')
            df.columns = df.columns.str.strip()

            if config["date_column"] not in df.columns:
                st.error(f"'{file_name}'に'{config['date_column']}'列が見つかりません。")
                return None
            
            df[config["date_column"]] = pd.to_datetime(df[config["date_column"]], errors='coerce')
            
            # 시험 결과 유효성 검사
            invalid_results = df[~df[config["result_column"]].isin(self.categories) & df[config["result_column"]].notna()]
            if not invalid_results.empty:
                for idx, row in invalid_results.iterrows():
                    self.invalid_results.append({
                        'file_name': file_name,
                        'test_id': row[config['test_id_column']],
                        'result': row[config['result_column']]
                    })
            
            # QA 상태와 QA_DB_NO 검사
            qa_without_no = df[
                (df[config["result_column"]] == 'QA') & 
                (df[config["qa_no_column"]].isna() | (df[config["qa_no_column"]] == ''))
            ]
            if not qa_without_no.empty:
                for idx, row in qa_without_no.iterrows():
                    self.qa_without_no.append({
                        'file_name': file_name,
                        'test_id': row[config['test_id_column']]
                    })
            
            # NG/BK 상태와 Bug_DB_NO 검사
            bug_without_no = df[
                (df[config["result_column"]].isin(['NG', 'BK'])) & 
                (df[config["bug_no_column"]].isna() | (df[config["bug_no_column"]] == ''))
            ]
            if not bug_without_no.empty:
                for idx, row in bug_without_no.iterrows():
                    self.bug_without_no.append({
                        'file_name': file_name,
                        'test_id': row[config['test_id_column']]
                    })
            
            return df
            
        except Exception as e:
            st.error(f"'{os.path.basename(file_path)}'の読み込み中にエラーが発生しました: {str(e)}")
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

    # 'OK'인 데이터를 날짜별로 집계한 테이블 생성 (config 사용)
    def _create_ok_table(self):
        config = self.config
        if self.merged_df.empty or config["date_column"] not in self.merged_df.columns:
            # merged_df가 비어있거나 필수 컬럼이 없으면 빈 DF 반환
            return pd.DataFrame(columns=[config["date_column"], 'OK']) 

        # 날짜 컬럼 NaT 제거 (pivot_table 오류 방지)
        df_filtered = self.merged_df.dropna(subset=[config["date_column"]])
        if df_filtered.empty:
             return pd.DataFrame(columns=[config["date_column"], 'OK'])

        # pivot_table 생성 시도
        try:
            pivot_table = df_filtered.pivot_table(
                index=config["date_column"],
                columns=config["result_column"],
                values=config["test_id_column"],
                aggfunc='count',
                fill_value=0
            )
        except KeyError as e:
             # 필요한 컬럼(result_column, test_id_column)이 없는 경우
             st.error(f"OK テーブル作成中にエラーが発生しました: 必要なカラムが見つかりません - {e}")
             return pd.DataFrame(columns=[config["date_column"], 'OK']) 
        
        # 'OK' 컬럼이 없는 경우 추가
        if 'OK' not in pivot_table.columns:
            pivot_table['OK'] = 0
            
        # 필요한 컬럼만 선택하여 반환 (다른 결과 컬럼은 필요 없음)
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
