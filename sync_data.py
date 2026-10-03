"""
sync_data.py
資料同步腳本：整合 CWA API 與 SQLite 資料庫 (data.db)
"""

import sys
from cwa_fetcher import fetch_realtime_observations, fetch_forecast_week, DEFAULT_API_KEY
from database import init_db, insert_observations, insert_forecasts, get_distinct_regions, get_weather_summary

def run_sync(api_key: str = DEFAULT_API_KEY):
    print("========================================")
    print("  中央氣象署 CWA 資料同步作業啟動")
    print("========================================")
    
    init_db()
    
    print("\n[1/2] 正在自 CWA API 擷取 O-A0003-001 全台即時測站資料...")
    stations = fetch_realtime_observations(api_key)
    if stations:
        inserted_obs = insert_observations(stations)
        print(f"-> 成功同步 {inserted_obs} 個氣象觀測站資料！")
    else:
        print("-> 警告：未取得觀測站資料。")

    print("\n[2/2] 正在自 CWA API 擷取一週氣溫預報資料...")
    forecasts = fetch_forecast_week(api_key)
    if forecasts:
        inserted_fc = insert_forecasts(forecasts)
        print(f"-> 成功同步 {inserted_fc} 筆氣候預報資料！")
    else:
        print("-> 警告：未取得預報資料。")

    print("\n========================================")
    print("  資料庫同步完成與驗證報告 (SQL Check)")
    print("========================================")
    regions = get_distinct_regions()
    print(f"可供查詢之地區清單 ({len(regions)} 個地區):")
    print("  ", ", ".join(regions[:8]) + ("..." if len(regions) > 8 else ""))
    
    stats = get_weather_summary()
    print(f"\n全台即時觀測摘要 (四宮格核心數據):")
    print(f"  有效測站數: {stats['station_count']}")
    print(f"  最高溫: {stats['max_temp']['val']} °C ({stats['max_temp']['station']})")
    print(f"  最低溫: {stats['min_temp']['val']} °C ({stats['min_temp']['station']})")
    print(f"  最大雨量: {stats['max_rain']['val']} mm ({stats['max_rain']['station']})")
    print(f"  最大風速: {stats['max_wind']['val']} m/s ({stats['max_wind']['station']})")
    print(f"  觀測資料時間: {stats['obs_time']}")
    print("========================================\n")

if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_API_KEY
    run_sync(key)
