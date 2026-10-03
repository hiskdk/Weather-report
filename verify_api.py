import requests, json

# 驗證修正後的兩個 API
print("=== /api/pm25 ===")
r = requests.get("http://localhost:8000/api/pm25", timeout=30)
d = r.json()
print("status:", d["status"])
print("count:", d["count"])
if d["stations"]:
    s = d["stations"][0]
    print("sample:", json.dumps(s, ensure_ascii=False))
    # 確認時間戳
    print("timestamp sample:", s.get("timestamp"))

print()
print("=== /api/weather ===")
r2 = requests.get("http://localhost:8000/api/weather", timeout=15)
d2 = r2.json()
print("status:", d2["status"])
print("stations:", len(d2.get("stations", [])))
s2 = d2.get("summary", {})
print("summary:", json.dumps(s2, ensure_ascii=False))
