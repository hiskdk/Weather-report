import requests

# 測試 MOENV 多個端點
tests = [
    "https://data.moenv.gov.tw/api/v2/aqx_p_432?format=json&limit=5&api_key=e8dd42e6-9b8b-43f8-991e-b3dee723a52d",
    # 嘗試不同的公開 key (來自 MOENV 開放資料平台說明頁)
    "https://data.moenv.gov.tw/api/v2/aqx_p_432?format=json&limit=5&api_key=9be7b239-557b-4c10-9775-78cadfc555e9",
    # 不帶 key 的版本
    "https://data.moenv.gov.tw/api/v2/aqx_p_432?format=json&limit=5",
    # 試試新版 API
    "https://airtw.moenv.gov.tw/cht/Query/InsertAnytime.aspx",
    # EPA 即時AQI CSV (可能開放)
    "https://data.moenv.gov.tw/api/v2/aqx_p_488?format=json&limit=3",
]

import socket
for h in ["data.moenv.gov.tw", "airtw.moenv.gov.tw"]:
    try:
        ip = socket.gethostbyname(h)
        print(f"{h} -> {ip}")
    except Exception as e:
        print(f"{h} -> FAIL: {e}")

print()
for url in tests[:3]:
    try:
        r = requests.get(url, timeout=8)
        print(f"[{r.status_code}] {url[:70]}")
        print(f"  CT: {r.headers.get('content-type','')[:50]}")
        print(f"  Body: {r.text[:150]}")
        print()
    except Exception as e:
        print(f"FAIL {url[:50]}: {e}\n")
