import io
import streamlit as st
import pandas as pd
from datetime import datetime
from config import load_config, save_config, DEFAULT_CONFIG
from folder_selector import select_folder
from data_collector import DataCollector, TestResult
from delivery_helper import DeliveryHelper
from ui_manager import UIManager
from business_manager import BusinessManager
from state_manager import StateManager

# 페이지 설정은 가장 먼저 호출되어야 함
st.set_page_config(layout="wide")

def main():
    # 의존성 주입
    config, full_config = load_config()
    ui_manager = UIManager()
    business_manager = BusinessManager(config)
    state_manager = StateManager()
    
    # 메뉴 선택
    choice = ui_manager.show_menu()
    
    if choice == "設定":
        # 설정 화면
        should_save, new_config = ui_manager.show_settings(config, full_config, DEFAULT_CONFIG)
        if should_save:
            business_manager.save_config(new_config)
    
    elif choice == "進捗管理":
        # 진도 관리 화면
        if ui_manager.show_progress_management(state_manager.get_test_result(), config):
            # 폴더 선택
            if not st.session_state.get("use_config_path", False):
                selected_folder_path = business_manager.select_folder()
                if selected_folder_path:
                    state_manager.set_folder_path(selected_folder_path)
            
            # 데이터 수집
            if state_manager.get_folder_path():
                test_result = business_manager.collect_data(state_manager.get_folder_path())
                state_manager.set_test_result(test_result)
        
        # 결과 표시
        ui_manager.display_test_results(state_manager.get_test_result(), config)
    
    elif choice == "納品作業":
        # 납품 작업 화면
        if ui_manager.show_delivery_work():
            # 폴더 선택
            selected_folder_path = business_manager.select_folder()
            if selected_folder_path:
                state_manager.set_folder_path(selected_folder_path)
            
            # 납품 작업 처리
            if state_manager.get_folder_path():
                business_manager.process_delivery(state_manager.get_folder_path())

if __name__ == "__main__":
    main()
