@echo off
chcp 65001 >nul
title 台灣即時氣象地圖 - CWA Open Data
echo ========================================================
echo   啟動 台灣即時氣象地圖 (Taiwan Weather Map)
echo   資料來源: 中央氣象署 CWA O-A0003-001 x SQLite (data.db)
echo ========================================================
echo.

REM 自動開啟預設瀏覽器到地圖服務
start http://localhost:8000

REM 啟動 Python Web 伺服器
if exist ".\.venv\Scripts\python.exe" (
    echo [INFO] 正在使用 Python 虛擬環境啟動伺服器 (Port: 8000)...
    ".\.venv\Scripts\python.exe" server.py 8000
) else (
    echo [INFO] 正在使用系統 Python 啟動伺服器 (Port: 8000)...
    python server.py 8000
)

pause
