

# TMT (Test Management Tool)
## 📋 プロジェクト概要
TMTは、**テストデータの管理および進捗分析ツール**であり、Excelベースのテストデータを自動で収集・分析し、プロジェクトの進捗状況を可視化するStreamlitウェブアプリケーションです。
QA業務を行う時、進捗把握や週次報告のために集計を取ることが多いです。

しかし、エクセルマクロなどを使って集計すると、毎回手作業が入るため、時間が浪費されていました。

このアプリケーションを利用すると、エクセルを開くことなくワンクリックで毎日の進捗状況や課題が一目で把握できます。

実際、毎回の集計に15分ほどかかっていましたが、毎日浪費される時間が減り、毎日の朝会や週次報告の準備にかかる時間が大幅に短縮できました。
![TMT_light](https://github.com/user-attachments/assets/3da8a872-45e6-4550-881c-9608a148dc71)


### 主な機能
- **📊 進捗管理**：テストデータの収集および分析を通じたリアルタイム進捗率モニタリング
- **⚙️ 設定管理**：データ収集パスや分析オプションなどのアプリケーション設定管理  
- **📦 納品作業**：最終成果物の整理および納品のためのデータ処理

## 🏗️ システムアーキテクチャ

### クラス構造

![TMT_class_diagram](https://github.com/user-attachments/assets/b1ebb663-5391-43dd-9cd3-6ec129c5d008)

### 設計思想
**レイヤードアーキテクチャ (Layered Architecture)**：階層化された責任分離
  - **プレゼンテーションレイヤー**: `UIManager` - UI表示とユーザー入力処理
  - **ビジネスレイヤー**: `BusinessManager` - 業務ロジックとワークフロー制御  
  - **データアクセスレイヤー**: `DataCollector`, `TableCreator` - データ収集・加工処理
  - **状態管理レイヤー**: `StateManager` - アプリケーション状態の永続化

### 設計パターン 
- **ストラテジーパターン (Strategy Pattern)**：`OKCalculator`インターフェースによる様々な計算方式の実装
- **依存性注入 (Dependency Injection)**：各マネージャークラス間の疎結合
- **単一責任の原則 (SRP)**：各クラスごとの明確な役割分担

## 🔄 主な機能の流れ

### 1. アプリケーション全体の流れ

[![](https://mermaid.ink/img/pako:eNp1lO9v0kAYx_-V5nzLCFDKoC9MNtjI2Niv-MrCiwauQAJ06Up0UpLRms2IU4xzGGVLWJhiFnCaLdHNhT_maDv-C48rYmtG01zueb6f73PP3aUtg5SYhoAFiaKQF5-ksrwkU48iiSKFnzlueFTTv9SS1MzMQ2qeQ1oLaTWknSHt97D603h5krRAa5wnWLhsx5DaR2obaY2KnQyPSGW4-8M4aJi9llnfU6gIZ4_Nw5vh8WnSjt91unrvo0ItcNbsHsS8PNDfVQe3TeOsq1CLnD124NYYIQ1HccPvkfoVaedI251szdFw1NYB0t4i9dfgtm8edpQYPpR9a5_6m9fDT3tJu8E4ukDVBqo-tzxWYYVa4u5dcTTHZ6WeIq2L1AtHq0uk1Zg9FSOpZQ6pHaR-Q-oNKYfrtsiJnxvtpnnp3PAysaxM6dkaVwgT_8eYV9_1-gsHEyfMqq3O_md8aQ5mlTBrnHlVN06ad62O2b52AGsEWOf03qvBtdO7QKSN8UUP-sd698MYWCTSpuNqJ6tbyLa8k4fUHCXk8nn2AfQKjADtyvpYSQVhIBWyKxtTlc2pSnisCIJAQ49dif6nABfISLk0YGWpBF2gAKUCPwpBeeRKADkLCzABWDxNQ4Ev5eUE_iwr2LbFFx-LYuGvUxJLmSxgBT6_jaPSVpqXYSTHZyS-MMlKsJiGUlgsFWXAen3eAKkC2DJ4imOGcc_SIY83GGQYfxC_LrCD07TH7WXoIB30-Gd9oQDNVFzgGVnY5_b4_Ewo4PP6fSG_n6ZxPZjOyaIUt_4f5DdS-QOxG8Th?type=png)](https://mermaid.live/edit#pako:eNp1lO9v0kAYx_-V5nzLCFDKoC9MNtjI2Niv-MrCiwauQAJ06Up0UpLRms2IU4xzGGVLWJhiFnCaLdHNhT_maDv-C48rYmtG01zueb6f73PP3aUtg5SYhoAFiaKQF5-ksrwkU48iiSKFnzlueFTTv9SS1MzMQ2qeQ1oLaTWknSHt97D603h5krRAa5wnWLhsx5DaR2obaY2KnQyPSGW4-8M4aJi9llnfU6gIZ4_Nw5vh8WnSjt91unrvo0ItcNbsHsS8PNDfVQe3TeOsq1CLnD124NYYIQ1HccPvkfoVaedI251szdFw1NYB0t4i9dfgtm8edpQYPpR9a5_6m9fDT3tJu8E4ukDVBqo-tzxWYYVa4u5dcTTHZ6WeIq2L1AtHq0uk1Zg9FSOpZQ6pHaR-Q-oNKYfrtsiJnxvtpnnp3PAysaxM6dkaVwgT_8eYV9_1-gsHEyfMqq3O_md8aQ5mlTBrnHlVN06ad62O2b52AGsEWOf03qvBtdO7QKSN8UUP-sd698MYWCTSpuNqJ6tbyLa8k4fUHCXk8nn2AfQKjADtyvpYSQVhIBWyKxtTlc2pSnisCIJAQ49dif6nABfISLk0YGWpBF2gAKUCPwpBeeRKADkLCzABWDxNQ4Ev5eUE_iwr2LbFFx-LYuGvUxJLmSxgBT6_jaPSVpqXYSTHZyS-MMlKsJiGUlgsFWXAen3eAKkC2DJ4imOGcc_SIY83GGQYfxC_LrCD07TH7WXoIB30-Gd9oQDNVFzgGVnY5_b4_Ewo4PP6fSG_n6ZxPZjOyaIUt_4f5DdS-QOxG8Th)

### 2. 進捗管理の詳細フロー
```
1. メニュー選択（進捗管理）
2. フォルダ選択（設定されたパス使用可否の確認）
3. 進捗管理画面の表示
4. 必要に応じてフォルダ選択
5. データ収集開始
   ├── Excelファイルの探索
   ├── データの統合
   └── データ処理
6. 結果分析
   ├── 累積OKデータの計算
   └── 別OKデータの計算 
7. 結果表示（テーブル＋チャート）
```

### 3. シーケンス図の主なインタラクション
- **ユーザー** ↔ **UIManager**：メニュー選択および画面表示
- **UIManager** ↔ **BusinessManager**：ビジネスロジックの実行リクエスト
- **BusinessManager** ↔ **StateManager**：状態情報の保存・参照
- **BusinessManager** ↔ **DataCollector**：データ収集および処理
- **DataCollector** ↔ **OKCalculator**：データ分析および計算
[![](https://mermaid.ink/img/pako:eNqtWGtTE1cY_is7-ylMIwMBlWQGZyCMM4xDHQp-qTiZNXsSdrrZjXsRqOMM2a1IRSptpbQVFahCwIJasViR5scccuFf9D1nLzmb3Viclg9hk_Nen_d69hafVUXEp3gd3TCRkkVDkpDXhMKEwsFfUdAMKSsVBcXgruhI4wSdw_Ymtj9g60_4jKAaJjRXhkcERcgjLUwwOEIIBk1dUpCuu2QcFyYco4RjhmCgtsKG0oRmSDCEtCrLKGuoEUTjlGhcuC6jtIaESJrLlygR_BPkrClHE12UZDQ2oxuo4OCwjK11bD3D9gtsHWDrL2zPYXttQnE4P1cNxKk3wTmCXJzhTnEns3_UFlfqe-v1pbna9tOGfXTy00J1a8HjJRxnLly4MpzisLWB7RVs72DrNcX9ANtb2H7TeHtQXVh2yYddYh0ZmSJAlcmqSk7Kx2RhRjWN_gl-ShLRBN_BkoMKkG6vY3sB289BdP3h4cnjjcZ6uf7sfYQhEzxr9QQf4D0pvavde8KIHxtJcXmwxkC6kdGQbspGzFU_NnLGFckcco3Kw-rifqs_k-pUpqipeSDSMwWaBgWk-KIYT1jjgp4QwuiQUHxJGLdJDO1Z3xH64xaFOyBAIIaWd6t7v2L7e4j48VGl_rDsnIXgcglLK7j01CHHpa2TR3ON8rwbbYLhKrYqEE5svSQxtm14YOR5QDjxhNgak7i0V939ubparm-8b-wsthAT3EkW5FRZRBpliDHMHRGydcBWUpWMTkqt09S97KEMXD83rpnIYUOyjrjjd7O1X6xI2NoAEU17OucHqT-ktF2XYowLgyNAwdZVm2DOkioldbSLrVdsWpC_Jv-ZgD4ksiAGlPrAfYyubTii2FynkCJGtI_hYPPA9l2amZXqg-8gnbB9WL27CVkfTNqIWmSNCNViyAdGAAEl6zTYjAjNNha2nIZiKJ3iFDQVbMgscdxNZJdpKO0yZTKSIhmZTCQ2HlOcu27mM7Kke57EuRsC-72DNdw3KGB4R3Q7GEq3QGyVSU5ahzSVmn3eQZyV0XSBIIyms0jO5ECSHmN9_EiOVufuQEV3Tsv6NKup9my1vr_hiAhmKFHG6Ll6jaPDAabPfLRhHgAOE4WB4Q8gIqtqkasufdPO_2Z2h91qw9LY2cWlSuPvD_DZruiImSRnLsLigVp0UBdgbIsZQRFhFiAYB1kyDagPMeJDa2djXTeVwAzSY2KOoWw-kc4OoTixy9hegi7hYxrtfkANSUsCK4dLZdruN48rj6FHN8lp43TEjw58imhI8FNIbmxvnpR_hMZ2CokUDCITl140KkfVe2ttCHWzUBA0CelA6Eyt-tul2pPVVibas9o2L1JZsFWxXcttVofV-bnak6V2o7YZxALSYKOheUsfRfrc2kK8oxxMLOgXWcGI-a52RAv2MincGZgMIhsjyjhgzFDSHMlSprwDeAFJLiRpHI4HzTy7gvqu5OJ-_rR0x3GP1bXBIOyx5iGTffQoUu3oQDutbmr5Sj3WU6oF9mitLGzqV0H2JlreSYidJkvaLJAlXLqJ2I28M-s-opjH3gIZUHsiaKsQNBSILnOeNQsQsVgHRxJ7b6V57o0N3wTiRURQqZQhQZJn_n8bXRtEIr2Neq9njkOSf0F72_HRam1-iQWazO0gjT8bwxs4qd2o1cNZr93ap7tTu5L1N0pR0otw9Qg2XuZLCyIt3H43q84_d9TCytnY3GIXN2bxb9YdzKAf_DZDjLR_J8_2Wvgm4CvLeLaKyAC0fWvDFwzHFGy9INc8ax-6uLderjqbKzT1sCK1aARuzLh0v7H9pr7vrqGNzVLttRW5N7fTx31GrmJrd-qP9lhJE3zEag_T0UCa1xb94r_qeEk2A7OgcP39zVUW-ibKq9rMtVZpFANWHuurPwNCqLEzlQ0jF_P7VkcYL0J9Spgc4vryTvXBAQNQWEYkQLT10siz-MC43aJJ_hu921fo5QRuKa8iQWFkfAomowNBPLyGGoJjdOCUUIwOhGAI8kZCQObAf0SgKeJfAWBLLjspaNGltv-yvr14-RLdw2BVXm5T-rWV59Aj2tC1anVHkrsFq1OKrApihPLgIgtXx03iOVwdSSv51r-zBt-TfNrLnure_eP3cI3g43xek0Q-ZcAVO84D-gWBfOVvEakTvDGJYB_myR1aRDmBNGmI4G1gKwrKl6pa8Dg11cxP8qmcANtgnDeLME-8F3n-rxrEA2lpshHzqe5ksptK4VO3-Gn43pfs7E70JBOJ3vNdPd1dXYk4PwM_J3o7e7uS55J9ybOJ7nN9Pedux_mvqeKezr6us72JxPm-RF_yfLI3GeeRKMEEHHHeJ9LXirf_AZnBLMs?type=png)](https://mermaid.live/edit#pako:eNqtWGtTE1cY_is7-ylMIwMBlWQGZyCMM4xDHQp-qTiZNXsSdrrZjXsRqOMM2a1IRSptpbQVFahCwIJasViR5scccuFf9D1nLzmb3Viclg9hk_Nen_d69hafVUXEp3gd3TCRkkVDkpDXhMKEwsFfUdAMKSsVBcXgruhI4wSdw_Ymtj9g60_4jKAaJjRXhkcERcgjLUwwOEIIBk1dUpCuu2QcFyYco4RjhmCgtsKG0oRmSDCEtCrLKGuoEUTjlGhcuC6jtIaESJrLlygR_BPkrClHE12UZDQ2oxuo4OCwjK11bD3D9gtsHWDrL2zPYXttQnE4P1cNxKk3wTmCXJzhTnEns3_UFlfqe-v1pbna9tOGfXTy00J1a8HjJRxnLly4MpzisLWB7RVs72DrNcX9ANtb2H7TeHtQXVh2yYddYh0ZmSJAlcmqSk7Kx2RhRjWN_gl-ShLRBN_BkoMKkG6vY3sB289BdP3h4cnjjcZ6uf7sfYQhEzxr9QQf4D0pvavde8KIHxtJcXmwxkC6kdGQbspGzFU_NnLGFckcco3Kw-rifqs_k-pUpqipeSDSMwWaBgWk-KIYT1jjgp4QwuiQUHxJGLdJDO1Z3xH64xaFOyBAIIaWd6t7v2L7e4j48VGl_rDsnIXgcglLK7j01CHHpa2TR3ON8rwbbYLhKrYqEE5svSQxtm14YOR5QDjxhNgak7i0V939ubparm-8b-wsthAT3EkW5FRZRBpliDHMHRGydcBWUpWMTkqt09S97KEMXD83rpnIYUOyjrjjd7O1X6xI2NoAEU17OucHqT-ktF2XYowLgyNAwdZVm2DOkioldbSLrVdsWpC_Jv-ZgD4ksiAGlPrAfYyubTii2FynkCJGtI_hYPPA9l2amZXqg-8gnbB9WL27CVkfTNqIWmSNCNViyAdGAAEl6zTYjAjNNha2nIZiKJ3iFDQVbMgscdxNZJdpKO0yZTKSIhmZTCQ2HlOcu27mM7Kke57EuRsC-72DNdw3KGB4R3Q7GEq3QGyVSU5ahzSVmn3eQZyV0XSBIIyms0jO5ECSHmN9_EiOVufuQEV3Tsv6NKup9my1vr_hiAhmKFHG6Ll6jaPDAabPfLRhHgAOE4WB4Q8gIqtqkasufdPO_2Z2h91qw9LY2cWlSuPvD_DZruiImSRnLsLigVp0UBdgbIsZQRFhFiAYB1kyDagPMeJDa2djXTeVwAzSY2KOoWw-kc4OoTixy9hegi7hYxrtfkANSUsCK4dLZdruN48rj6FHN8lp43TEjw58imhI8FNIbmxvnpR_hMZ2CokUDCITl140KkfVe2ttCHWzUBA0CelA6Eyt-tul2pPVVibas9o2L1JZsFWxXcttVofV-bnak6V2o7YZxALSYKOheUsfRfrc2kK8oxxMLOgXWcGI-a52RAv2MincGZgMIhsjyjhgzFDSHMlSprwDeAFJLiRpHI4HzTy7gvqu5OJ-_rR0x3GP1bXBIOyx5iGTffQoUu3oQDutbmr5Sj3WU6oF9mitLGzqV0H2JlreSYidJkvaLJAlXLqJ2I28M-s-opjH3gIZUHsiaKsQNBSILnOeNQsQsVgHRxJ7b6V57o0N3wTiRURQqZQhQZJn_n8bXRtEIr2Neq9njkOSf0F72_HRam1-iQWazO0gjT8bwxs4qd2o1cNZr93ap7tTu5L1N0pR0otw9Qg2XuZLCyIt3H43q84_d9TCytnY3GIXN2bxb9YdzKAf_DZDjLR_J8_2Wvgm4CvLeLaKyAC0fWvDFwzHFGy9INc8ax-6uLderjqbKzT1sCK1aARuzLh0v7H9pr7vrqGNzVLttRW5N7fTx31GrmJrd-qP9lhJE3zEag_T0UCa1xb94r_qeEk2A7OgcP39zVUW-ibKq9rMtVZpFANWHuurPwNCqLEzlQ0jF_P7VkcYL0J9Spgc4vryTvXBAQNQWEYkQLT10siz-MC43aJJ_hu921fo5QRuKa8iQWFkfAomowNBPLyGGoJjdOCUUIwOhGAI8kZCQObAf0SgKeJfAWBLLjspaNGltv-yvr14-RLdw2BVXm5T-rWV59Aj2tC1anVHkrsFq1OKrApihPLgIgtXx03iOVwdSSv51r-zBt-TfNrLnure_eP3cI3g43xek0Q-ZcAVO84D-gWBfOVvEakTvDGJYB_myR1aRDmBNGmI4G1gKwrKl6pa8Dg11cxP8qmcANtgnDeLME-8F3n-rxrEA2lpshHzqe5ksptK4VO3-Gn43pfs7E70JBOJ3vNdPd1dXYk4PwM_J3o7e7uS55J9ybOJ7nN9Pedux_mvqeKezr6us72JxPm-RF_yfLI3GeeRKMEEHHHeJ9LXirf_AZnBLMs)

## 🛠️ 技術スタック
### Backend
- **Python 3.8**：メイン開発言語
- **Streamlit**：Web UIフレームワーク
- **OpenPyXL**: Excelファイル読み取り・修正・スタイリング
- **XlsxWriter**: Excelファイル生成・ダウンロード
- **Pandas**：データ処理および分析
- **Tkinter**: フォルダー選択ダイアログ (Python 標準ライブラリ)

### Frontend
- **Streamlit Components**：インタラクティブなWebインターフェース
- **Charts & Visualization**：進捗率の可視化

### Development Tools
- **Git**：バージョン管理
- **Virtual Environment**：パッケージ依存関係の管理
- **JSON**：設定ファイル管理

## 🚀 インストールおよび実行方法
### 1. 環境設定
```bash
# リポジトリをクローン
git clone [repository-url]
cd TMT

# 仮想環境の作成および有効化
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 2. 実行
```bash
# Streamlitアプリの起動
streamlit run main.py
```

### 3. バッチファイル実行（Windowsの場合）
```bash
# 環境設定
1_setup.bat

# データ収集開始
2_startCollect.bat
```

## 📁 プロジェクト構成
```
TMT/
├── main.py               # メイン実行ファイル
├── ui_manager.py         # UI管理モジュール
├── business_manager.py   # ビジネスロジックモジュール
├── state_manager.py      # 状態管理モジュール
├── data_collector.py     # データ収集モジュール
├── table_creator.py      # テーブル作成モジュール
├── delivery_helper.py    # 納品サポートモジュール
├── config.py             # 設定管理モジュール
├── config.json           # 設定ファイル
├── requirements.txt      # パッケージ依存関係
├── 1_setup.bat           # 環境設定バッチファイル
├── 2_startCollect.bat    # 実行バッチファイル
├── tests/                # テストファイル群
├── test_data/            # テスト用データ
└── packages/             # 追加パッケージ
```

## 🎯 主要な実装ポイント
### 1. モジュール化されたアーキテクチャ
- **関心の分離**：UI、ビジネスロジック、データ処理をそれぞれ独立したモジュールで実装
- **拡張性**：新しい計算方式を追加する場合、`OKCalculator`インターフェースを実装するだけでOK

### 2. 柔軟なデータ処理
- **様々なExcelフォーマットに対応**：フォルダ構成に応じた自動データ検出
- **リアルタイム分析**：データ変更時に即時再計算＆可視化

### 3. ユーザーフレンドリーなインターフェース
- **直感的なメニュー構成**：設定、進捗管理、納品作業で明確に区分
- **ビジュアルフィードバック**：チャートやテーブルによるデータ可視化

## 📈 開発成果
- **コード再利用性**：インターフェースベースの設計により高い再利用性を実現
- **保守性**：単一責任の原則による明確なモジュール分離
- **拡張性**：新しい分析方式の追加が容易
- **ユーザビリティ**：Streamlitを活用した直感的なWebインターフェースを提供


---



**본 프로젝트는 실제 업무 환경에서의 테스트 관리 요구사항을 분석하여 개발된 실용적인 도구입니다.**
