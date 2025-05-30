import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import pytest
from datetime import datetime
from data_collector import (
    DataCollector, 
    DataTestResult, 
    DailyOKCalculator, 
    CumulativeOKCalculator
)

def test_merge_data():
    """DataFrame 병합이 정상적으로 동작하는지 테스트"""
    # mock dataframe 2개 생성 (컬럼 일부 다르게)
    df1 = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
    df2 = pd.DataFrame({'A': [5, 6], 'C': [7, 8]})

    # DataCollector 인스턴스 생성
    dc = DataCollector(selected_folder_path="", config={})

    # _merge_data는 DataFrame의 리스트를 받아야 함
    result = dc._merge_data([df1, df2])

    # 결과 검증
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 4
    # 컬럼 존재 여부 및 값 확인
    assert list(result['A']) == [1, 2, 5, 6]
    assert list(result['B'][:2]) == [3, 4]
    assert all(pd.isna(x) for x in result['B'][2:])
    assert all(pd.isna(x) for x in result['C'][:2])
    assert list(result['C'][2:]) == [7, 8]

def test_merge_data_empty():
    """DataFrame 병합이 빈 리스트 입력시 빈 DataFrame을 반환하는지 테스트"""
    dc = DataCollector(selected_folder_path="", config={})

    result = dc._merge_data([])

    # 결과 검증
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0

def test_daily_ok_calculator():
    """일별 OK 계산 전략 테스트"""
    # 테스트 데이터 생성
    df = pd.DataFrame({
        'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'OK': [5, 3, 7]
    })
    config = {'date_column': 'date'}
    
    calculator = DailyOKCalculator()
    result = calculator.calculate(df, config)
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert list(result.columns) == ['date', 'OK']
    assert list(result['OK']) == [5, 3, 7]

def test_cumulative_ok_calculator():
    """누적 OK 계산 전략 테스트"""
    # 테스트 데이터 생성
    df = pd.DataFrame({
        'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'OK': [5, 3, 7]
    })
    config = {'date_column': 'date'}
    
    calculator = CumulativeOKCalculator()
    result = calculator.calculate(df, config)
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert list(result.columns) == ['date', 'OK_cumulative']
    assert list(result['OK_cumulative']) == [5, 8, 15]

def test_ok_calculator_empty_data():
    """빈 데이터프레임에 대한 OK 계산 전략 테스트"""
    df = pd.DataFrame()
    config = {'date_column': 'date'}
    
    daily_calculator = DailyOKCalculator()
    cumulative_calculator = CumulativeOKCalculator()
    
    daily_result = daily_calculator.calculate(df, config)
    cumulative_result = cumulative_calculator.calculate(df, config)
    
    assert isinstance(daily_result, pd.DataFrame)
    assert isinstance(cumulative_result, pd.DataFrame)
    assert len(daily_result) == 0
    assert len(cumulative_result) == 0

def test_test_result_dataclass():
    """DataTestResult 데이터클래스 테스트"""
    # 빈 DataFrame들 생성
    empty_df = pd.DataFrame()
    
    # DataTestResult 인스턴스 생성
    result = DataTestResult(
        summary_df=empty_df,
        merged_df=empty_df,
        bug_table=empty_df,
        qa_table=empty_df,
        ok_table=empty_df,
        cumulative_ok_df=empty_df,
        daily_ok_df=empty_df
    )
    
    # 속성 검증
    assert isinstance(result.summary_df, pd.DataFrame)
    assert isinstance(result.merged_df, pd.DataFrame)
    assert isinstance(result.bug_table, pd.DataFrame)
    assert isinstance(result.qa_table, pd.DataFrame)
    assert isinstance(result.ok_table, pd.DataFrame)
    assert isinstance(result.cumulative_ok_df, pd.DataFrame)
    assert isinstance(result.daily_ok_df, pd.DataFrame)

@pytest.fixture
def sample_config():
    """테스트용 설정 데이터"""
    return {
        'date_column': 'date',
        'result_column': 'result',
        'bug_no_column': 'bug_no',
        'qa_no_column': 'qa_no',
        'test_id_column': 'test_id',
        'test_name_column': 'test_name',
        'bug_file_name': 'bug_list.xlsx',
        'qa_file_name': 'qa_list.xlsx',
        'sheet_name': 'Sheet1',
        'bug_file_columns': ['description'],
        'qa_file_columns': ['description'],
        'bug_pattern_template': '내부버그#{Int}',
        'qa_pattern_template': '내부QA#{Int}',
        'bug_regex': '내부버그#(\\d+)',
        'qa_regex': '내부QA#(\\d+)'
    }

@pytest.fixture
def sample_test_data():
    """테스트용 데이터프레임"""
    return pd.DataFrame({
        'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'result': ['OK', 'NG', 'OK'],
        'bug_no': ['B001', None, 'B002'],
        'qa_no': [None, 'Q001', None]
    })

def test_data_collector_initialization(sample_config):
    """DataCollector 초기화 테스트"""
    dc = DataCollector(
        selected_folder_path="/test/path",
        config=sample_config,
        bug_list_folder="/test/bug",
        qa_list_folder="/test/qa"
    )
    
    assert dc.selected_folder_path == "/test/path"
    assert dc.bug_list_folder == "/test/bug"
    assert dc.qa_list_folder == "/test/qa"
    assert dc.config == sample_config
    assert isinstance(dc.results, list)
    assert isinstance(dc.summaries, list)
    assert isinstance(dc.merged_df, pd.DataFrame)
    assert isinstance(dc.invalid_results, list)
    assert isinstance(dc.qa_without_no, list)
    assert isinstance(dc.bug_without_no, list)

def test_count_test_results(sample_config, sample_test_data):
    """테스트 결과 카운트 테스트"""
    dc = DataCollector(selected_folder_path="", config=sample_config)
    counts = dc._count_test_results(sample_test_data)
    
    assert isinstance(counts, dict)
    assert counts['OK'] == 2
    assert counts['NG'] == 1
    assert counts['BK'] == 0
    assert counts['NY'] == 0
    assert counts['TS'] == 0
    assert counts['QA'] == 0
    assert counts['NT'] == 0

def test_invalid_folder_path():
    """잘못된 폴더 경로에 대한 테스트"""
    dc = DataCollector(selected_folder_path="/invalid/path", config={})
    result = dc.collect_data()
    
    assert isinstance(result, DataTestResult)
    assert len(result.summary_df) == 0
    assert len(result.merged_df) == 0
    assert len(result.bug_table) == 0
    assert len(result.qa_table) == 0
    assert len(result.ok_table) == 0
    assert len(result.cumulative_ok_df) == 0
    assert len(result.daily_ok_df) == 0

@pytest.fixture
def sample_excel_files(tmp_path):
    """테스트용 엑셀 파일들 생성"""
    # 테스트 데이터 생성 (시험표용)
    test_data = pd.DataFrame({
        'test_id': ['T001', 'T002'],
        'test_name': ['Test 1', 'Test 2'],
        'date': ['2024-01-01', '2024-01-02'],
        'result': ['OK', 'NG'],
        'bug_no': ['B001', None],
        'qa_no': [None, 'Q001']
    })
    
    # 버그 데이터 생성 (一覧 시트용)
    bug_data = pd.DataFrame({
        'No': [1, 2],
        'description': ['Bug 1', 'Bug 2']
    })
    
    # QA 데이터 생성 (一覧 시트용)  
    qa_data = pd.DataFrame({
        'No': [1, 2],
        'description': ['QA 1', 'QA 2']
    })
    
    # 엑셀 파일 생성
    test_file = tmp_path / "test.xlsx"
    bug_file = tmp_path / "bug_list.xlsx"
    qa_file = tmp_path / "qa_list.xlsx"
    
    # 시험표는 Sheet1에 저장
    test_data.to_excel(test_file, sheet_name='Sheet1', index=False)
    # 버그/QA 리스트는 一覧 시트에 저장
    bug_data.to_excel(bug_file, sheet_name='一覧', index=False)
    qa_data.to_excel(qa_file, sheet_name='一覧', index=False)
    
    return {
        'test_file': str(test_file),
        'bug_file': str(bug_file),
        'qa_file': str(qa_file),
        'tmp_path': str(tmp_path)
    }

def test_read_and_preprocess_excel(sample_config, sample_excel_files):
    """엑셀 파일 읽기 및 전처리 테스트"""
    dc = DataCollector(
        selected_folder_path=sample_excel_files['tmp_path'],
        config=sample_config
    )
    
    # 테스트 파일 읽기
    df = dc._read_and_preprocess_excel(sample_excel_files['test_file'])
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    expected_columns = ['test_id', 'test_name', 'date', 'result', 'bug_no', 'qa_no']
    assert all(col in df.columns for col in expected_columns)
    assert list(df['result']) == ['OK', 'NG']
    assert df['bug_no'].iloc[0] == 'B001'
    assert pd.isna(df['bug_no'].iloc[1])  # NaN 체크
    assert pd.isna(df['qa_no'].iloc[0])   # NaN 체크
    assert df['qa_no'].iloc[1] == 'Q001'

def test_collect_excel_data(sample_config, sample_excel_files):
    """엑셀 데이터 수집 테스트"""
    dc = DataCollector(
        selected_folder_path=sample_excel_files['tmp_path'],
        config=sample_config
    )
    
    # 모든 엑셀 파일 경로
    excel_files = [
        sample_excel_files['test_file'],
        sample_excel_files['bug_file'],
        sample_excel_files['qa_file']
    ]
    
    # 데이터 수집
    test_data = dc._collect_excel_data(excel_files)
    
    assert isinstance(test_data, list)
    assert len(test_data) == 1  # 테스트 파일만 포함
    assert isinstance(dc.bug_data, pd.DataFrame)
    assert isinstance(dc.qa_data, pd.DataFrame)
    assert len(dc.bug_data) == 2
    assert len(dc.qa_data) == 2

def test_process_data(sample_config, sample_excel_files):
    """데이터 처리 테스트"""
    dc = DataCollector(
        selected_folder_path=sample_excel_files['tmp_path'],
        config=sample_config
    )
    
    # 테스트 데이터 설정
    dc.merged_df = pd.DataFrame({
        'test_id': ['T001', 'T002'],
        'date': pd.to_datetime(['2024-01-01', '2024-01-02']),
        'result': ['OK', 'NG'],
        'bug_no': ['B001', None],
        'qa_no': [None, 'Q001']
    })
    
    # summaries 데이터 추가 (summary_df 생성을 위해 필요)
    dc.summaries = [{
        'file_name': 'test.xlsx',
        'OK': 1,
        'NG': 1,
        'BK': 0,
        'NY': 0,
        'TS': 0,
        'QA': 0,
        'NT': 0
    }]
    
    # bug_data와 qa_data를 None으로 설정하여 table creator 우회
    dc.bug_data = None
    dc.qa_data = None
    
    # 데이터 처리
    result = dc._process_data()
    
    assert isinstance(result, DataTestResult)
    assert len(result.summary_df) > 0
    assert len(result.merged_df) == 2
    # bug_table과 qa_table은 external data가 없으면 빈 DataFrame일 수 있음
    assert isinstance(result.bug_table, pd.DataFrame)
    assert isinstance(result.qa_table, pd.DataFrame)
    assert len(result.ok_table) > 0
    assert len(result.cumulative_ok_df) > 0
    assert len(result.daily_ok_df) > 0

def test_get_excel_files(sample_config, sample_excel_files):
    """엑셀 파일 목록 가져오기 테스트"""
    dc = DataCollector(
        selected_folder_path=sample_excel_files['tmp_path'],
        config=sample_config
    )
    
    excel_files = dc._get_excel_files()
    
    assert isinstance(excel_files, list)
    assert len(excel_files) == 3  # test.xlsx, bug_list.xlsx, qa_list.xlsx
    assert all(file.endswith('.xlsx') for file in excel_files)