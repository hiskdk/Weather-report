# 🌤️ 台灣即時氣象地圖 (Taiwan Weather Map)
> **中央氣象署 CWA Open Data 即時視覺化地圖（O-A0003-001 全台測站觀測）**  
> 專案結合 **CWA API** × **Python** × **SQLite (`data.db`)** × **Leaflet.js** × **Streamlit**

---

## 📸 介面設計說明

本專案依據 [taiwan-weather-map.vercel.app](https://taiwan-weather-map.vercel.app) 規格 100% 像素級還原：
1. **全螢幕沉浸式暗黑 GIS 地圖**：使用 Esri World Dark Gray Base + Reference 圖資，完美呈現深色高質感地圖。
2. **左上方即時氣象與四宮格指標卡**：
   - 觀測時間、資料來源（CWA O-A0003-001）、本次讀取狀態、測站總數。
   - 2×2 四宮格極值統計：最高溫（測站）、最低溫（測站）、最大雨量（測站）、最大風速（測站）。
3. **頂部中央警特報膠囊**：
   - ⚠️ 天氣特報（強風、降雨、雷雨），支援一鍵展開/收合詳細特報內文。
4. **右側圖層與底圖控制面板**：
   - **圖層切換**：🌡️ 氣溫、🌧️ 雨量、🛰️ 雷達、🌀 颱風、💨 風速風向、💧 濕度（支援選中高亮）、⛅ 天氣、📍 測站點位。
   - **開關選項**：縣市界線、數值/氣溫標籤。
   - **底圖切換**：深色 / 街道圖 (OpenStreetMap)。
   - **📌 定位我的位置**：一鍵瀏覽器 GPS 定位。
5. **中央/測站彈出浮動卡片 (Popup Card)**：
   - 顯示測站名稱、縣市/鄉鎮、觀測時間。
   - 包含：氣溫、相對濕度、測站氣壓、風速、風向、最大瞬間風、雨量、天氣現象。
6. **右下方動態色階圖例**：
   - 依當前選中圖層自動切換單位與漸層條（如濕度 `%` 40~90、氣溫 `°C` 5~36 等）。
7. **左下方狀態欄**：
   - 更新時間與「🔄 重新整理」按鈕，點擊即時重新呼叫 CWA API 並同步 SQLite 資料庫。

---

## 🚀 啟動方式

### 方法 1：Windows 直接雙擊啟動（最推薦）
在資料夾中直接滑鼠雙擊 **`run.bat`**，會自動開啟瀏覽器前往 `http://localhost:8000` 並呈現完整全螢幕氣象地圖！

### 方法 2：終端機啟動 Web 服務
```bash
.\.venv\Scripts\python.exe server.py 8000
```
瀏覽器開啟：`http://localhost:8000`

### 方法 3：Streamlit 啟動（符合課綱驗證需求）
```bash
.\.venv\Scripts\python.exe -m streamlit run app.py
```
瀏覽器開啟：`http://localhost:8501`

---

## 📂 檔案目錄結構

```text
天氣預報/
├── index.html          # 全螢幕暗黑 GIS 氣象地圖前端 (100% 還原台灣即時氣象地圖)
├── server.py           # 輕量高效 Web 伺服器與 REST API (/api/weather, /api/refresh)
├── app.py              # Streamlit 整合版應用程式 (含作業資料庫驗證折疊面板)
├── cwa_fetcher.py      # 中央氣象署 API 資料擷取 (O-A0003-001, F-C0032, 特報)
├── database.py         # SQLite (data.db) 操作與資料表結構維護
├── sync_data.py        # 資料庫資料同步與驗證腳本
├── data.db             # SQLite 資料庫 (儲存 StationObservations 與預報)
├── run.bat             # Windows 一鍵啟動腳本
├── requirements.txt    # Python 依賴套件
└── README.md           # 專案手冊
```
