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
        
        pivot_test_names = (
            filtered_df.groupby(self.config["bug_no_column"]).apply(
                lambda group: pd.Series({
                    self.config["test_name_column"]: ', '.join(sorted(set(group[self.config["test_name_column"]].dropna().astype(str))))
                })
            ).reset_index()
        )
        
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
        if external_data is None:
            return pivot_df
            
        def extract_bug_number(bug_db_no):
            if pd.isna(bug_db_no):
                return None
            match = re.search(self.config["bug_regex"], str(bug_db_no))
            return int(match.group(1)) if match else None
            
        # 시험표의 버그 번호 추출
        pivot_df['BugNumber'] = pivot_df[self.config["bug_no_column"]].apply(extract_bug_number)
        external_data['No'] = pd.to_numeric(external_data['No'], errors='coerce')
        
        # 외부 데이터를 기준으로 병합 (모든 버그 항목 표시)
        merged_result = pd.merge(pivot_df, external_data, left_on='BugNumber', right_on='No', how='right')
        
        # 시험표에 없는 항목은 0으로 설정
        merged_result['件数'] = merged_result['件数'].fillna(0)
        merged_result[self.config["test_name_column"]] = merged_result[self.config["test_name_column"]].fillna('')
        
        # 불필요한 컬럼 제거
        merged_result = merged_result.drop(columns=['No', 'BugNumber'])
        if self.config["bug_no_column"] in merged_result.columns:
            merged_result = merged_result.drop(columns=[self.config["bug_no_column"]])
        
        # 버그 번호 다시 생성
        merged_result[self.config["bug_no_column"]] = external_data.apply(
            lambda row: f"内部バグ#{row['No']}", axis=1
        )
        
        final_columns = [self.config["bug_no_column"], "JIRA#", '件数', 
                        self.config["test_name_column"], 'ステータス', '概要']
        return merged_result[final_columns]

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
        
        pivot_test_names = (
            filtered_df.groupby(self.config["qa_no_column"]).apply(
                lambda group: pd.Series({
                    self.config["test_name_column"]: ', '.join(sorted(set(group[self.config["test_name_column"]].dropna().astype(str))))
                })
            ).reset_index()
        )
        
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
        if external_data is None:
            return pivot_df
            
        def extract_qa_number(qa_db_no):
            match = re.search(self.config["qa_regex"], str(qa_db_no))
            return int(match.group(1)) if match else None
            
        pivot_df['QANumber'] = pivot_df[self.config["qa_no_column"]].apply(extract_qa_number)
        external_data['No'] = pd.to_numeric(external_data['No'], errors='coerce')
        
        merged_result = pd.merge(pivot_df, external_data, left_on='QANumber', right_on='No', how='left')
        merged_result = merged_result.drop(columns=['QANumber', 'No'])
        
        final_columns = [self.config["qa_no_column"], '件数', 
                        self.config["test_name_column"], '質問者', 'コメント', 
                        '回答', 'ステータス']
        return merged_result[final_columns] 