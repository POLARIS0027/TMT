@echo off
chcp 65001 > nul
echo [1/4] 仮想環境(venv) 生成中...
python -m venv venv

echo [2/4] 仮想環境活性化...
call venv\Scripts\activate

echo [3/4] パッケージ設置中...
pip install --no-index --find-links=packages -r requirements.txt

echo [4/4] 設置完了! startCollect.batを実行してください。
pause
