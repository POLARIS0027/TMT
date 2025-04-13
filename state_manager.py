import streamlit as st

class StateManager:
    """상태 관리를 담당하는 클래스"""
    
    def __init__(self):
        if 'folder_path' not in st.session_state:
            st.session_state.folder_path = ""
        if 'test_result' not in st.session_state:
            st.session_state.test_result = None
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        if 'selected_bug' not in st.session_state:
            st.session_state.selected_bug = None
        if 'selected_qa' not in st.session_state:
            st.session_state.selected_qa = None
    
    def get_folder_path(self):
        """폴더 경로 가져오기"""
        return st.session_state.folder_path
    
    def set_folder_path(self, path):
        """폴더 경로 설정"""
        st.session_state.folder_path = path
    
    def get_test_result(self):
        """테스트 결과 가져오기"""
        return st.session_state.test_result
    
    def set_test_result(self, result):
        """테스트 결과 설정"""
        st.session_state.test_result = result
        st.session_state.data_loaded = True
    
    def is_data_loaded(self):
        """데이터 로드 여부 확인"""
        return st.session_state.data_loaded
    
    def get_selected_bug(self):
        """선택된 버그 가져오기"""
        return st.session_state.selected_bug
    
    def set_selected_bug(self, bug):
        """선택된 버그 설정"""
        st.session_state.selected_bug = bug
    
    def get_selected_qa(self):
        """선택된 QA 가져오기"""
        return st.session_state.selected_qa
    
    def set_selected_qa(self, qa):
        """선택된 QA 설정"""
        st.session_state.selected_qa = qa 