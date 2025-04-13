# 시험 관리 도구 개발자 가이드

## 1. 프로젝트 구조 개요
이 프로젝트는 시험 결과를 관리하고 분석하는 웹 애플리케이션입니다. 주요 기능은 다음과 같습니다:
- 시험 결과 데이터 수집 및 분석
- 결과 시각화 (그래프, 테이블)
- 납품용 엑셀 파일 자동 포맷팅

## 2. 주요 파일 및 클래스 설명

### 2.1 main.py - 메인 애플리케이션
애플리케이션의 진입점이며, 전체 흐름을 제어합니다.

```python
def main():
    # 1. 각 매니저 클래스 초기화
    # 2. 메뉴 선택에 따른 화면 표시
    # 3. 사용자 입력 처리
```

### 2.2 ui_manager.py - UI 관리자
사용자 인터페이스를 담당하는 `UIManager` 클래스가 있습니다.

#### UIManager 클래스의 주요 메소드:
1. `show_menu()`: 
   - 역할: 좌측 사이드바에 메인 메뉴 표시
   - 반환값: 선택된 메뉴 ("進捗管理", "納品作業", "設定" 중 하나)

2. `show_settings(config, full_config, DEFAULT_CONFIG)`:
   - 역할: 설정 화면 표시 및 설정값 저장
   - 매개변수:
     - config: 현재 설정값
     - full_config: 전체 설정 정보
     - DEFAULT_CONFIG: 기본 설정값
   - 반환값: (설정 저장 여부, 새로운 설정값)

3. `show_progress_management(test_result, config)`:
   - 역할: 진도 관리 화면 표시
   - 주요 기능:
     - 설정된 폴더 경로 표시
     - 임시 폴더 선택 기능
     - 데이터 수집 실행 버튼
   - 매개변수:
     - test_result: 테스트 결과 데이터
     - config: 현재 설정값

4. `show_delivery_work()`:
   - 역할: 납품 작업 화면 표시
   - 기능:
     - 수동 작업 가이드 표시
     - 자동 포맷팅 실행 버튼

5. `display_test_results(test_result, config)`:
   - 역할: 테스트 결과 데이터 표시
   - 표시 항목:
     - 시험표별 결과 일람
     - 상세 데이터
     - OK 건수 그래프
     - 누적 그래프
     - 엑셀 다운로드 버튼

### 2.3 business_manager.py - 비즈니스 로직 관리자
실제 데이터 처리와 비즈니스 로직을 담당하는 `BusinessManager` 클래스가 있습니다.

#### BusinessManager 클래스의 주요 메소드:
1. `collect_data(selected_folder_path)`:
   - 역할: 선택된 폴더에서 데이터 수집 및 처리
   - 반환값: TestResult 객체

2. `process_delivery(selected_folder_path)`:
   - 역할: 납품용 엑셀 파일 자동 포맷팅
   - 처리 내용:
     - 빈 셀 채우기
     - 셀 정렬
     - 폰트 설정
     - 확대/축소 비율 설정

### 2.4 state_manager.py - 상태 관리자
애플리케이션의 상태를 관리하는 `StateManager` 클래스가 있습니다.

#### StateManager 클래스의 주요 메소드:
1. `get_folder_path()`, `set_folder_path(path)`:
   - 역할: 선택된 폴더 경로 관리

2. `get_test_result()`, `set_test_result(result)`:
   - 역할: 테스트 결과 데이터 관리

### 2.5 data_collector.py - 데이터 수집기
엑셀 파일에서 데이터를 수집하고 처리하는 `DataCollector` 클래스가 있습니다.

#### DataCollector 클래스의 주요 메소드:
1. `collect_data()`:
   - 역할: 데이터 수집 및 처리 파이프라인 실행
   - 처리 단계:
     - 엑셀 파일 검색
     - 데이터 읽기 및 전처리
     - 데이터 병합
     - 결과 생성

## 3. 주요 데이터 흐름
1. 사용자가 메뉴 선택
2. 선택된 메뉴에 따라 해당 화면 표시
3. 사용자 입력(폴더 선택, 버튼 클릭 등) 처리
4. 비즈니스 로직 실행
5. 결과 표시

## 4. 코드 수정 가이드
### 4.1 UI 수정하기
- `ui_manager.py`의 해당 메소드 수정
- Streamlit 위젯 사용 (`st.button()`, `st.selectbox()` 등)
- 각 위젯에 고유한 `key` 값 부여 필수

### 4.2 데이터 처리 로직 수정하기
- `data_collector.py`의 해당 메소드 수정
- pandas DataFrame 활용
- 에러 처리 추가 필수

### 4.3 새로운 기능 추가하기
1. 해당 기능의 UI 메소드를 `UIManager` 클래스에 추가
2. 필요한 비즈니스 로직을 `BusinessManager` 클래스에 추가
3. `main.py`에서 새로운 기능 연결

## 5. 주의사항
- 모든 파일 경로 존재 여부 확인 필수
- 에러 메시지는 사용자가 이해하기 쉽게 작성
- 큰 데이터 처리 시 성능 고려
- 각 클래스의 단일 책임 원칙 준수 

## 6. 상태 관리 상세 설명

### 6.1 Streamlit의 세션 상태 (st.session_state)
Streamlit 앱에서는 `st.session_state`를 통해 페이지가 다시 로드되어도 유지되어야 하는 데이터를 관리합니다.

#### 기본 사용법:
```python
# 상태 저장
st.session_state.folder_path = "C:/some/path"

# 상태 읽기
current_path = st.session_state.get("folder_path", "")  # 기본값 ""
```

#### 주요 세션 상태 변수:
1. `folder_path`: 선택된 폴더 경로
   ```python
   # 저장
   st.session_state.folder_path = selected_path
   
   # 읽기
   path = st.session_state.get("folder_path", "")
   ```

2. `test_result`: 수집된 테스트 결과
   ```python
   # 저장
   st.session_state.test_result = test_result
   
   # 읽기
   result = st.session_state.get("test_result", None)
   ```

3. `data_loaded`: 데이터 로드 상태
   ```python
   # 데이터 로드 완료 표시
   st.session_state.data_loaded = True
   
   # 로드 상태 확인
   is_loaded = st.session_state.get("data_loaded", False)
   ```

### 6.2 StateManager 클래스
세션 상태 관리를 편리하게 하기 위해 `StateManager` 클래스를 사용합니다.

#### 역할:
- 세션 상태 변수에 대한 일관된 접근 방법 제공
- 상태 변경 로직 중앙 집중화
- 타입 안정성 확보

#### 사용 예시:
```python
# StateManager 초기화
state_manager = StateManager()

# 폴더 경로 저장
state_manager.set_folder_path("C:/some/path")

# 폴더 경로 읽기
current_path = state_manager.get_folder_path()

# 테스트 결과 저장
state_manager.set_test_result(test_result)

# 테스트 결과 읽기
current_result = state_manager.get_test_result()
```

### 6.3 상태 관리 흐름
1. 초기 상태:
   ```python
   # main.py
   state_manager = StateManager()  # 상태 관리자 초기화
   ```

2. 폴더 선택 시:
   ```python
   # 폴더 선택 후
   if selected_folder_path:
       state_manager.set_folder_path(selected_folder_path)
   ```

3. 데이터 수집 시:
   ```python
   # 데이터 수집 후
   test_result = business_manager.collect_data(state_manager.get_folder_path())
   state_manager.set_test_result(test_result)
   ```

4. UI 업데이트 시:
   ```python
   # 결과 표시
   ui_manager.display_test_results(state_manager.get_test_result(), config)
   ```

### 6.4 주의사항
1. 세션 상태 초기화:
   - 앱 시작 시 필요한 세션 상태 변수 초기화
   - 기본값 설정 필수

2. 상태 변경 시점:
   - 중요한 데이터 변경 시에만 상태 업데이트
   - 불필요한 상태 저장 지양

3. 에러 처리:
   - 상태 읽기 시 항상 기본값 설정
   - 상태 없는 경우 대비

4. 성능 고려:
   - 큰 데이터는 필요한 부분만 상태로 관리
   - 임시 데이터는 일반 변수 사용

### 6.5 디버깅 팁
1. 현재 세션 상태 확인:
   ```python
   st.write("Current Session State:", st.session_state)
   ```

2. 특정 상태 변수 확인:
   ```python
   st.write("Folder Path:", st.session_state.get("folder_path"))
   st.write("Data Loaded:", st.session_state.get("data_loaded"))
   ```

3. 상태 초기화:
   ```python
   # 특정 상태 삭제
   if "folder_path" in st.session_state:
       del st.session_state.folder_path
   
   # 전체 상태 초기화
   for key in list(st.session_state.keys()):
       del st.session_state[key]
   ``` 