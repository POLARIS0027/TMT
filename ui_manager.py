import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os

class UIManager:
    """UI 관련 로직을 담당하는 클래스"""
    
    def __init__(self):
        pass  # set_page_config() 제거
    
    def show_menu(self):
        """메뉴 표시"""
        menu = ["進捗管理", "納品作業", "設定"]
        return st.sidebar.selectbox("Menu", menu, key="main_menu")
    
    def show_settings(self, config, full_config, DEFAULT_CONFIG):
        """설정 화면 표시"""
        st.title("設定")
        st.write("以下の項目を編集して、ユーザー設定を行ってください。\n(設定値は config.json に保存され、再起動時も保持されます。)")
        
        if st.button("⚠️ 設定を初期化（リセット）"):
            full_config["user_config"] = {}
            return True, full_config
        
        user_config = full_config.get("user_config", {})
        updated_config = {}
        
        with st.form(key="user_config_form"):
            for key, default_value in DEFAULT_CONFIG.items():
                current_value = user_config.get(key, default_value)
                
                if isinstance(default_value, list):
                    value = st.text_area(
                        f"{key} (カンマ区切り)", 
                        value=", ".join(current_value) if isinstance(current_value, list) else str(current_value),
                        key=f"settings_{key}"
                    )
                    updated_config[key] = [v.strip() for v in value.split(",") if v.strip()]
                else:
                    updated_config[key] = st.text_input(key, value=str(current_value), key=f"settings_{key}")
            
            submitted = st.form_submit_button("💾 保存")
        
        if submitted:
            full_config["user_config"] = updated_config
            return True, full_config
        
        return False, full_config
    
    def show_progress_management(self, test_result, config):
        """진도 관리 화면 표시"""
        st.title("試験管理Tool 1.0.1")
        
        # 설정된 기본 경로 표시
        config_path = config.get("selected_folder_path", "")
        if config_path:
            if os.path.exists(config_path):
                st.info(f"設定で指定されたデフォルトパス: {config_path}")
            else:
                st.warning(f"設定で指定されたパス '{config_path}' が存在しません。設定画面で正しいパスを指定してください。")
        
        st.write("一時的なフォルダーから読み込む場合、フォルダーを指定してください。")
        
        # 임시 폴더 선택 UI
        selected_folder_path = st.session_state.get("folder_path", "")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("フォルダー選択", key="select_folder_btn"):
                st.session_state.use_config_path = False
                return True
                
        with col2:
            if st.button("設定したパスで集計開始", key="use_config_path_btn"):
                if not config_path:
                    st.error("設定でパスが指定されていません。設定画面でパスを指定してください。")
                    return False
                elif not os.path.exists(config_path):
                    st.error(f"設定で指定されたパス '{config_path}' が存在しません。設定画面で正しいパスを指定してください。")
                    return False
                else:
                    st.session_state.folder_path = config_path
                    st.session_state.use_config_path = True
                    st.session_state.should_collect = True
                    st.rerun()
                    return True
        
        if selected_folder_path:
            if not os.path.exists(selected_folder_path):
                st.error(f"選択されたパス '{selected_folder_path}' が存在しません。")
                st.session_state.folder_path = ""
                return False
                
            st.write("選択したフォルダー:", selected_folder_path)
            st.write("集計実施を押してください。")
            if st.button("集計実施", key="collect_data_btn") or st.session_state.get("should_collect", False):
                st.session_state.should_collect = False
                return True
        
        return False
    
    def show_delivery_work(self):
        """납품 작업 화면 표시"""
        st.title("納品作業Helper 1.0.0")
        st.markdown('<p style="color:blue; font-weight:bold;">Step.1 (マニュアル作業)</p>', unsafe_allow_html=True)
        st.text("１．不要な列を削除する")
        st.text("２．実施者フォーマット一致させる")
        st.text("３．表紙を足す")
        st.text("４．シートのはみだしなどを確認する。")
        st.markdown('<p style="color:blue; font-weight:bold;">Step.2 (自動作業)</p>', unsafe_allow_html=True)
        st.text("１．\"試験表\" 空白を '-'で埋める")
        st.text("２．\"試験表\" シートの全てのセルを左上に整列させる")
        st.text("３．全てのシートのフォントを 'メイリオ'で統一")
        st.text("４．全てのシートの拡大割合を100%に設定する")
        
        selected_folder_path = st.session_state.get("folder_path", "")
        if st.button("フォルダー選択", key="delivery_select_folder_btn"):
            return True
        
        if selected_folder_path and st.button("納品作業Step.2をスタート", key="delivery_process_btn"):
            return True
        
        return False
    
    def display_test_results(self, test_result, config):
        """테스트 결과 표시"""
        if test_result is None:
            return
        
        # 요약 데이터 표시
        st.markdown("<h4 style='color: #567ace; font-weight: bold;'>試験表別結果一覧</h4>", unsafe_allow_html=True)
        st.dataframe(test_result.summary_df, use_container_width=True, hide_index=True)
        
        # 시험표 상세 데이터 표시
        self._display_detail_results(test_result, config)
        
        # 버그 테이블 표시
        st.markdown("<h4 style='color: #567ace; font-weight: bold;'>内部バグ一覧</h4>", unsafe_allow_html=True)
        if not test_result.bug_table.empty:
            st.dataframe(test_result.bug_table, use_container_width=True, hide_index=True)
            # 버그 상세보기
            bug_numbers = sorted(test_result.bug_table[config["bug_no_column"]].dropna().unique().tolist())
            if bug_numbers:
                col1, col2 = st.columns([1, 4])
                with col1:
                    selected_bug = st.selectbox("表示したいバグ番号を選択してください", bug_numbers, key="bug_select")
                    show_bug = st.button("バグ詳細表示", key="show_bug_detail_btn")
                if show_bug:
                    bug_detail = test_result.merged_df[
                        (test_result.merged_df[config["bug_no_column"]] == selected_bug) &
                        (test_result.merged_df[config["result_column"]].isin(['NG', 'BK']))
                    ]
                    if not bug_detail.empty:
                        st.dataframe(bug_detail, use_container_width=True, hide_index=True)
                    else:
                        st.warning("選択したバグ番号のデータがありません")
        else:
            st.write("内部バグデータがありません")
        
        # QA 테이블 표시
        st.markdown("<h4 style='color: #567ace; font-weight: bold;'>内部QA一覧</h4>", unsafe_allow_html=True)
        if not test_result.qa_table.empty:
            st.dataframe(test_result.qa_table, use_container_width=True, hide_index=True)
            # QA 상세보기
            qa_numbers = sorted(test_result.qa_table[config["qa_no_column"]].dropna().unique().tolist())
            if qa_numbers:
                col1, col2 = st.columns([1, 4])
                with col1:
                    selected_qa = st.selectbox("表示したいQA番号を選択してください", qa_numbers, key="qa_select")
                    show_qa = st.button("QA詳細表示", key="show_qa_detail_btn")
                if show_qa:
                    qa_detail = test_result.merged_df[
                        (test_result.merged_df[config["qa_no_column"]] == selected_qa) &
                        (test_result.merged_df[config["result_column"]] == 'QA')
                    ]
                    if not qa_detail.empty:
                        st.dataframe(qa_detail, use_container_width=True, hide_index=True)
                    else:
                        st.warning("選択したQA番号のデータがありません")
        else:
            st.write("内部QAデータがありません")
        
        # 그래프 표시
        self._display_charts(test_result, config)
        
        # 엑셀 다운로드 버튼
        self._create_excel_download(test_result)
    
    def _display_detail_results(self, test_result, config):
        """상세 결과 표시"""
        col1, col2 = st.columns([1, 4])
        with col1:
            result_categories = sorted(test_result.merged_df[config["result_column"]].dropna().unique().tolist())
            selected_category = st.selectbox("表示したい試験結果を選択してください", result_categories, key="result_category")
            show_detail = st.button("項目詳細表示", key="show_detail_btn")
        
        if show_detail:
            detail_df = test_result.merged_df[test_result.merged_df[config["result_column"]] == selected_category]
            if not detail_df.empty:
                st.dataframe(detail_df, use_container_width=True, hide_index=True)
            else:
                st.warning("選択したカテゴリーのデータがありません")
    
    def _display_charts(self, test_result, config):
        """차트 표시"""
        # 날짜별 시험 결과 일람 (전체 카테고리)
        st.markdown("<h4 style='color: #567ace; font-weight: bold;'>日付別試験結果一覧</h4>", unsafe_allow_html=True)
        if not test_result.merged_df.empty and config["date_column"] in test_result.merged_df.columns:
            # 날짜별로 그룹화하여 각 결과 카테고리별 개수 계산
            date_summary = test_result.merged_df.pivot_table(
                index=config["date_column"],
                columns=config["result_column"],
                values=config["test_id_column"],
                aggfunc='count',
                fill_value=0
            ).reset_index()
            
            # 날짜 형식 조정
            date_summary[config["date_column"]] = date_summary[config["date_column"]].dt.strftime('%Y-%m-%d')
            
            # 누계 행 추가
            total_row = {}
            total_row[config["date_column"]] = "累計"
            
            # 각 결과 카테고리별 합계 계산
            for col in date_summary.columns:
                if col != config["date_column"]:
                    total_row[col] = date_summary[col].sum()
            
            # 누계 행을 데이터프레임으로 변환하고 기존 데이터프레임에 추가
            total_df = pd.DataFrame([total_row])
            date_summary_with_total = pd.concat([date_summary, total_df], ignore_index=True)
            
            # 각 날짜별 합계 열 추가
            result_columns = [col for col in date_summary_with_total.columns if col != config["date_column"]]
            date_summary_with_total['消化項目数'] = date_summary_with_total[result_columns].sum(axis=1)
            
            # 누계 행을 위한 스타일링 인덱스 확인 (마지막 행)
            last_row_idx = len(date_summary_with_total) - 1
            
            # 테이블 표시 - 컬럼 너비 조정 및 누계 행 강조
            column_config = {
                config["date_column"]: st.column_config.TextColumn("実施日", width="small"),
            }
            
            # 시험 결과 컬럼 너비 설정
            for col in result_columns:
                column_config[col] = st.column_config.NumberColumn(col, width="small")
            
            # 합계 컬럼 너비 설정
            column_config['消化項目数'] = st.column_config.NumberColumn("消化項目数", width="small")
            
            # 누계 행 강조 스타일 함수
            def highlight_last_row(row):
                if row.name == last_row_idx:
                    return ['background-color: #E7F0FD; font-weight: bold; border-top: 2px solid #0066CC'] * len(row)
                return [''] * len(row)
            
            # 스타일이 적용된 데이터프레임 생성
            styled_df = date_summary_with_total.style.apply(highlight_last_row, axis=1)
            
            # 테이블 표시
            st.dataframe(
                styled_df,
                column_config=column_config,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.write("試験データがありません")
        
        # 일별 OK 그래프
        st.markdown("<h4 style='color: #567ace; font-weight: bold;'>日付別 OK件数</h4>", unsafe_allow_html=True)
        if not test_result.daily_ok_df.empty:
            plot_daily_ok_df = self._prepare_date_data(test_result.daily_ok_df, config)
            st.bar_chart(data=plot_daily_ok_df.set_index(config["date_column"])['OK'])
        else:
            st.write("日付別 OK データがありません")
        
        # 누적 OK 그래프
        st.markdown("<h4 style='color: #567ace; font-weight: bold;'>OKの累積グラフ</h4>", unsafe_allow_html=True)
        if not test_result.cumulative_ok_df.empty:
            plot_cumulative_ok_df = self._prepare_date_data(test_result.cumulative_ok_df, config)
            st.line_chart(data=plot_cumulative_ok_df.set_index(config["date_column"])['OK_cumulative'])
        else:
            st.write("OK 累積データがありません")
    
    def _prepare_date_data(self, df, config):
        """날짜 데이터 전처리"""
        if not pd.api.types.is_datetime64_any_dtype(df[config["date_column"]]):
            df[config["date_column"]] = pd.to_datetime(df[config["date_column"]], errors='coerce')
        df.dropna(subset=[config["date_column"]], inplace=True)
        plot_df = df.copy()
        plot_df[config["date_column"]] = plot_df[config["date_column"]].dt.strftime('%Y-%m-%d')
        return plot_df
    
    def _create_excel_download(self, test_result):
        """엑셀 다운로드 생성"""
        todayhhmm = datetime.today().strftime('%Y%m%d_%H%M')
        result_filename = f'result_{todayhhmm}.xlsx'
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            test_result.summary_df.to_excel(writer, index=False, sheet_name='試験表別結果一覧')
            test_result.merged_df.to_excel(writer, index=False, sheet_name='統合シート')
            test_result.daily_ok_df.to_excel(writer, index=False, sheet_name='日々のOK数グラフ')
            test_result.cumulative_ok_df.to_excel(writer, index=False, sheet_name='OK累計グラフ')
            if not test_result.bug_table.empty:
                test_result.bug_table.to_excel(writer, index=False, sheet_name='内部バグ一覧')
            if not test_result.qa_table.empty:
                test_result.qa_table.to_excel(writer, index=False, sheet_name='内部QA一覧')
        
        writer.close()
        data = output.getvalue()
        
        st.download_button(
            label="Excelファイルダウンロード",
            data=data,
            file_name=result_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="excel_download_btn"
        ) 