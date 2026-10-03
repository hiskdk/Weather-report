import requests

# 測試其他可能有 PM2.5 資料的免費 API
tests = [
    # LASS 不同端點 - 嘗試取最新的
    "https://pm25.lass-net.org/API-1.0.0/project/airbox/latest/?fields=device_id,gps_lat,gps_lon,s_d0,s_t0,s_h0,timestamp",
    # LASS 其他 project
    "https://pm25.lass-net.org/API-1.0.0/project/all/latest/?limit=5",
    # OpenAQ (全球開放空品)
    "https://api.openaq.org/v2/measurements?location_id=242150&limit=5&parameter=pm25",
    # AirVisual / IQAir 公開端點
    "https://aqicn.org/map/taiwan/",
    # 嘗試 LASS 不同子集 - 每日最新
    "https://pm25.lass-net.org/API-1.0.0/project/airbox/year/2026/month/10/day/03/",
]

for url in tests[:4]:
    try:
        r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        print(f"[{r.status_code}] {url[:75]}")
        ct = r.headers.get('content-type','')
        if 'json' in ct:
            import json
            try:
                d = r.json()
                k = list(d.keys())[:5] if isinstance(d, dict) else "list"
                print(f"  Keys: {k}")
                feeds = d.get('feeds') or d.get('results') or d.get('data') or []
                print(f"  Count: {len(feeds) if isinstance(feeds, list) else type(feeds)}")
                if isinstance(feeds, list) and feeds:
                    print(f"  Sample: {str(feeds[0])[:150]}")
            except:
                print(f"  Body: {r.text[:150]}")
        else:
            print(f"  CT: {ct[:50]}")
            print(f"  Body: {r.text[:100]}")
        print()
    except Exception as e:
        print(f"FAIL: {url[:60]}: {e}\n")
