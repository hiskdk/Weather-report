"""
server.py
中央氣象署即時地圖與資料庫整合 Web 伺服器
提供：
1. 靜態網頁服務 (提供與 taiwan-weather-map 一致之全螢幕地圖前端)
2. /api/weather: 提供最新即時測站與四宮格極值、天氣特報
3. /api/pm25:  Proxy 至 LASS AirBox，回傳全台 PM2.5 即時資料 (5 分鐘快取)
4. /api/refresh: 即時從 CWA API 更新並同步寫入 SQLite 資料庫 (data.db)
"""

import json
import os
import sys
import time
import threading
import requests
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from database import init_db, get_all_stations, get_weather_summary, get_all_forecasts_dict, get_distinct_regions, get_forecasts_by_region
from cwa_fetcher import fetch_weather_warnings
from sync_data import run_sync

# ---- PM2.5 快取 ----
_pm25_cache = {"data": None, "ts": 0}
_pm25_lock = threading.Lock()
PM25_CACHE_TTL = 300  # 5 分鐘

AIRBOX_URL = "https://pm25.lass-net.org/API-1.0.0/project/airbox/latest/"

def _fetch_pm25_data():
    """向 LASS AirBox API 取 PM2.5，清洗後回傳列表"""
    import datetime
    try:
        resp = requests.get(AIRBOX_URL, timeout=15)
        resp.encoding = 'utf-8'
        resp.raise_for_status()
        raw = resp.json()
        feeds = raw.get("feeds", [])
        result = []
        now_utc = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

        for f in feeds:
            lat = f.get("gps_lat")
            lon = f.get("gps_lon")
            pm25 = f.get("s_d0")
            if lat is None or lon is None or pm25 is None:
                continue
            try:
                lat, lon, pm25 = float(lat), float(lon), float(pm25)
            except (ValueError, TypeError):
                continue

            # 只保留台灣範圍內
            if not (21.5 <= lat <= 25.5 and 119.5 <= lon <= 122.5):
                continue

            # PM2.5 合理範圍（AirBox 感測器在台灣通常 0–200，>200 視為感測器異常）
            if pm25 < 0 or pm25 > 200:
                continue

            # ── 時間記錄（不過濾，LASS API 為快照資料）──
            ts_str = f.get("timestamp", "")
            # 只計算資料齡，用於 log，不過濾
            data_age_note = ""
            if ts_str:
                try:
                    ts_dt = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    age_h = (now_utc - ts_dt).total_seconds() / 3600
                    data_age_note = f"{age_h:.0f}h"
                except Exception:
                    pass

            # 溫度合理範圍 (台灣 AirBox 感測器)
            temp = f.get("s_t0")
            temp_val = None
            if temp is not None:
                try:
                    tv = float(temp)
                    if 5.0 <= tv <= 45.0:  # 台灣氣溫合理範圍
                        temp_val = round(tv, 1)
                except (ValueError, TypeError):
                    pass

            # 濕度合理範圍
            humi = f.get("s_h0")
            humi_val = None
            if humi is not None:
                try:
                    hv = float(humi)
                    if 1.0 <= hv <= 100.0:
                        humi_val = round(hv, 1)
                except (ValueError, TypeError):
                    pass

            result.append({
                "name": f.get("SiteName") or f.get("name") or f.get("device_id", ""),
                "area": f.get("area", ""),
                "lat": lat,
                "lon": lon,
                "pm25": round(pm25, 1),
                "temp": temp_val,
                "humidity": humi_val,
                "timestamp": ts_str,
                "device_id": f.get("device_id", ""),
            })

        print(f"[PM2.5] 取得 {len(feeds)} 筆，清洗後 {len(result)} 筆有效資料")
        return result
    except Exception as e:
        print(f"AirBox fetch error: {e}")
        return []

def get_pm25_cached():
    """帶快取的 PM2.5 取得"""
    with _pm25_lock:
        now = time.time()
        if _pm25_cache["data"] is not None and (now - _pm25_cache["ts"]) < PM25_CACHE_TTL:
            return _pm25_cache["data"]
        data = _fetch_pm25_data()
        if data:  # 成功才更新快取
            _pm25_cache["data"] = data
            _pm25_cache["ts"] = now
        return _pm25_cache["data"] or []

import math

def sanitize_json(val):
    """遞迴清除 NaN、Infinity 與非原生型別，確保輸出嚴格合法之 JSON"""
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    elif isinstance(val, dict):
        return {k: sanitize_json(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [sanitize_json(v) for v in val]
    elif hasattr(val, 'item'):
        v = val.item()
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        return v
    return val

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class WeatherMapHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        
        # 0. PM2.5 API
        if parsed.path == '/api/pm25':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            data = get_pm25_cached()
            payload = sanitize_json({"status": "success", "count": len(data), "stations": data})
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
            return

        # 1. API: 取得氣象資料
        if parsed.path == '/api/weather':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            # 從 SQLite 讀取測站資料
            df_stations = get_all_stations()
            stations_list = df_stations.to_dict(orient='records')
            
            # 四宮格極值統計
            raw = get_weather_summary()
            def _v(x):
                if isinstance(x, dict):
                    return x.get('val', '--')
                return x if x is not None else '--'

            flat_summary = {
                "max_temp":   _v(raw.get('max_temp')),
                "min_temp":   _v(raw.get('min_temp')),
                "max_rain":   _v(raw.get('max_rain')),
                "avg_wind":   _v(raw.get('max_wind')),
                "station_count": raw.get('station_count', 0),
                "max_temp_station": raw.get('max_temp', {}).get('station', '') if isinstance(raw.get('max_temp'), dict) else '',
                "min_temp_station": raw.get('min_temp', {}).get('station', '') if isinstance(raw.get('min_temp'), dict) else '',
            }
            
            # 天氣特報
            warnings = fetch_weather_warnings()

            # 一週氣溫預報 (步驟 13-16)
            forecasts = get_all_forecasts_dict()

            payload = {
                "status": "success",
                "summary": flat_summary,
                "warnings": warnings,
                "stations": stations_list,
                "forecasts": forecasts
            }
            clean_payload = sanitize_json(payload)
            self.wfile.write(json.dumps(clean_payload, ensure_ascii=False).encode('utf-8'))
            return

        # 1.5 API: 取得一週預報專屬端點 (步驟 13-16)
        if parsed.path == '/api/forecasts':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            forecasts = get_all_forecasts_dict()
            regions = get_distinct_regions()
            payload = sanitize_json({"status": "success", "regions": regions, "forecasts": forecasts})
            self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
            return

        # 2. 根目錄與 index.html
        if parsed.path in ('/', '/index.html', ''):
            index_file = os.path.join(BASE_DIR, 'index.html')
            if os.path.exists(index_file):
                with open(index_file, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            self.path = '/index.html'
            return super().do_GET()

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        
        # 重新整理/同步資料庫
        if parsed.path == '/api/refresh':
            try:
                run_sync()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": "資料已更新至 SQLite"}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

def run_server(port=PORT):
    # 確保資料庫初始化
    init_db()
    
    server_address = ('', port)
    httpd = ThreadingHTTPServer(server_address, WeatherMapHandler)
    print(f"========================================================")
    print(f"  台灣即時氣象地圖 Web 服務已啟動")
    print(f"  本機網址: http://localhost:{port}")
    print(f"  資料庫檔案: {os.path.join(BASE_DIR, 'data.db')}")
    print(f"========================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n伺服器已停止。")
        httpd.server_close()

if __name__ == '__main__':
    p = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(p)
