import os
import json

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "selected_folder_path": "",
    "bug_list_folder": "",
    "qa_list_folder": "",
    "sheet_name": "試験表",
    "date_column": "実施日",
    "result_column": "試験結果",
    "test_id_column": "試験項目ID",
    "test_name_column": "試験名",
    "bug_no_column": "バグ_DB_No",
    "qa_no_column": "Q&A_DB_No",
    "bug_file_name": "内部バグリスト.xlsx",
    "qa_file_name": "内部QAリスト.xlsx",
    "qa_pattern_template": "内部QA#{Int}",
    "bug_pattern_template": "内部バグ#{Int}",
    "qa_regex": "内部QA#(\\d+)",
    "bug_regex": "内部バグ#(\\d+)",
    "bug_file_columns": ["No", "ステータス", "概要", "JIRA#"],
    "qa_file_columns": ["No", "コメント", "質問者", "回答", "ステータス"]
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        _create_default_config_file()

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        full_config = json.load(f)

    # ensure 함수 호출
    full_config, changed = ensure_all_keys_present(full_config)
    if changed:
        save_config(full_config)  # 누락된 항목 채워졌으면 저장

    # 병합된 설정 반환
    merged = full_config["default_config"].copy()
    merged.update(full_config["user_config"])
    return merged, full_config

def _create_default_config_file():
    full_config = {
        "default_config": DEFAULT_CONFIG.copy(),
        "user_config": {}
    }
    save_config(full_config)

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

# 누락된 필드 자동 채우고 저장까지 해주는 유틸 함수
def ensure_all_keys_present(full_config):
    changed = False
    if "default_config" not in full_config:
        full_config["default_config"] = DEFAULT_CONFIG.copy()
        changed = True
    if "user_config" not in full_config:
        full_config["user_config"] = {}
        changed = True
    for key in DEFAULT_CONFIG:
        if key not in full_config["default_config"]:
            full_config["default_config"][key] = DEFAULT_CONFIG[key]
            changed = True
    return full_config, changed
