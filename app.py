"""
app.py
台灣即時氣象地圖 (Taiwan Weather Map) - Streamlit 整合版
- 完美還原台灣即時氣象地圖 (taiwan-weather-map.vercel.app) 全螢幕沉浸式暗黑 GIS 設計
- 完整包含 SQLite 資料庫 (data.db) 與中央氣象署 CWA O-A0003-001 即時連線
- 符合作業學習地圖 24 步驟規範
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import os
import pandas as pd

from database import init_db, get_all_stations, get_weather_summary, get_forecasts_by_region, get_distinct_regions, get_connection
from cwa_fetcher import fetch_weather_warnings, fetch_realtime_observations, fetch_forecast_week
from database import insert_observations, insert_forecasts

st.set_page_config(
    page_title="台灣即時氣象地圖",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 極致隱藏 Streamlit 預設邊框與頂部 Header，實現 100% 全螢幕無縫地圖體驗
st.markdown("""
<style>
    /* 隱藏 Streamlit 默認元素 */
    #MainMenu { visibility: hidden; display: none; }
    header { visibility: hidden; display: none; }
    footer { visibility: hidden; display: none; }
    .stAppDeployButton { display: none !important; }
    
    /* 移除多餘 padding */
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        max-width: 100% !important;
    }
    
    /* 全螢幕 iframe 設定 */
    iframe {
        border: none !important;
        width: 100vw !important;
        height: 100vh !important;
        display: block !important;
    }
</style>
""", unsafe_allow_html=True)

# 確保資料庫初始化
init_db()

# 取得最新資料庫內容
df_stations = get_all_stations()
if df_stations.empty:
    obs = fetch_realtime_observations()
    if obs:
        insert_observations(obs)
    fc = fetch_forecast_week()
    if fc:
        insert_forecasts(fc)
    df_stations = get_all_stations()

stations_list = df_stations.to_dict(orient='records')
summary = get_weather_summary()
warnings = fetch_weather_warnings()

weather_payload = {
    "status": "success",
    "summary": summary,
    "warnings": warnings,
    "stations": stations_list
}

# 讀取 index.html 並注入初始資料庫快取
index_path = os.path.join(os.path.dirname(__file__), "index.html")
with open(index_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# 注入資料快取，保證即使在 Streamlit iframe 沙盒中也能零延遲立即呈現
injection = f"window.INITIAL_DATA = {json.dumps(weather_payload, ensure_ascii=False)};"
html_content = html_content.replace("window.INITIAL_DATA = null;", injection)

# 渲染全螢幕地圖組件
components.html(html_content, height=920, scrolling=False)

# 底部可選摺疊面板：供作業檢查 SQLite 資料表與一週預報 (符合課程 8~16 步驟)
with st.expander("📚 點此展開：作業 24 步驟資料庫 (SQLite data.db) 與一週預報驗證面板"):
    st.markdown("### 🗄️ SQLite 資料庫查詢驗證")
    tab_a, tab_b = st.tabs(["一週預報資料 (TemperatureForecasts)", "即時測站資料 (StationObservations)"])
    
    with tab_a:
        regions = get_distinct_regions() or ["北部地區", "中部地區", "南部地區"]
        sel_reg = st.selectbox("選擇預報地區：", regions, index=0)
        fc_df = get_forecasts_by_region(sel_reg)
        st.dataframe(fc_df, use_container_width=True)
        
    with tab_b:
        st.dataframe(df_stations[["county", "town", "station_name", "temperature", "humidity", "air_pressure", "wind_speed", "precipitation", "weather"]], use_container_width=True)
