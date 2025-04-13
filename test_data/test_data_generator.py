import pandas as pd
import random
from datetime import datetime, timedelta

def generate_test_sheet(num_rows=50):
    # 시험표 데이터 생성
    data = {
        '試験項目ID': [f'TEST{i:03d}' for i in range(1, num_rows + 1)],
        '試験名': [f'機能テスト {i}' for i in range(1, num_rows + 1)],
        '実施日': [(datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d') for _ in range(num_rows)],
        '試験結果': random.choices(['合格', '不合格', '保留'], k=num_rows),
        'バグ_DB_No': [f'内部バグ#{random.randint(1, 30)}' if random.random() > 0.7 else '' for _ in range(num_rows)],
        'Q&A_DB_No': [f'内部QA#{random.randint(1, 40)}' if random.random() > 0.7 else '' for _ in range(num_rows)]
    }
    return pd.DataFrame(data)

def generate_bug_list(num_rows=30):
    # 버그 리스트 데이터 생성
    data = {
        'No': [f'BUG{i:03d}' for i in range(1, num_rows + 1)],
        'ステータス': random.choices(['新規', '対応中', '解決済', '確認済'], k=num_rows),
        '概要': [f'機能エラー {i}' for i in range(1, num_rows + 1)],
        'JIRA#': [f'JIRA-{random.randint(1000, 9999)}' if random.random() > 0.5 else '' for _ in range(num_rows)]
    }
    return pd.DataFrame(data)

def generate_qa_list(num_rows=40):
    # QA 리스트 데이터 생성
    data = {
        'No': [f'QA{i:03d}' for i in range(1, num_rows + 1)],
        'コメント': [f'品質検証項目 {i}' for i in range(1, num_rows + 1)],
        '質問者': random.choices(['山田太郎', '佐藤花子', '鈴木一郎', '田中次郎'], k=num_rows),
        '回答': [f'回答 {i}' for i in range(1, num_rows + 1)],
        'ステータス': random.choices(['待機', '対応中', '完了'], k=num_rows)
    }
    return pd.DataFrame(data)

if __name__ == '__main__':
    # 시험표 파일 3개 생성
    for i in range(1, 4):
        test_sheet = generate_test_sheet()
        with pd.ExcelWriter(f'試験表_{i}.xlsx', engine='openpyxl') as writer:
            test_sheet.to_excel(writer, sheet_name='試験表', index=False)
    
    # 버그 리스트 생성
    bug_list = generate_bug_list()
    with pd.ExcelWriter('内部バグリスト.xlsx', engine='openpyxl') as writer:
        bug_list.to_excel(writer, sheet_name='一覧', index=False)
    
    # QA 리스트 생성
    qa_list = generate_qa_list()
    with pd.ExcelWriter('内部QAリスト.xlsx', engine='openpyxl') as writer:
        qa_list.to_excel(writer, sheet_name='一覧', index=False)
    
    print("すべてのテストファイルが生成されました。") 