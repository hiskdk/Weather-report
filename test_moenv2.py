import requests

# 確認 MOENV 的 CORS header，看前端能否直接呼叫
url = "https://data.moenv.gov.tw/api/v2/aqx_p_432?format=json&limit=3"
r = requests.get(url, timeout=10)
print("Status:", r.status_code)
print("CORS headers:")
for k, v in r.headers.items():
    if 'cors' in k.lower() or 'access' in k.lower() or 'origin' in k.lower():
        print(f"  {k}: {v}")
print("Content-Type:", r.headers.get('content-type'))
print("Body (bytes):", r.content[:200])
# 用 big5 解碼試試
try:
    print("Body (big5):", r.content[:200].decode('big5'))
except:
    pass
try:
    print("Body (cp950):", r.content[:200].decode('cp950'))
except:
    pass
