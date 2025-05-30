from data_collector import DataCollector, DataTestResult
from delivery_helper import DeliveryHelper
from folder_selector import select_folder
from config import save_config

class BusinessManager:
    """비즈니스 로직을 담당하는 클래스"""
    
    def __init__(self, config):
        self.config = config
    
    def collect_data(self, selected_folder_path) -> DataTestResult:
        """데이터 수집 및 처리"""
        data_collector = DataCollector(
            selected_folder_path,
            self.config,
            bug_list_folder=self.config.get("bug_list_folder", ""),
            qa_list_folder=self.config.get("qa_list_folder", "")
        )
        return data_collector.collect_data()
    
    def process_delivery(self, selected_folder_path):
        """납품 작업 처리"""
        delivery_helper = DeliveryHelper(selected_folder_path)
        delivery_helper.fill_blank_cells_in_range()
        delivery_helper.align_cells_left_top()
        delivery_helper.set_font_to_meiryo()
        delivery_helper.set_zoom_to_100()
        return True
    
    def select_folder(self):
        """폴더 선택"""
        return select_folder()
    
    def save_config(self, full_config):
        """설정 저장"""
        save_config(full_config)
        return True 