import requests, datetime

r = requests.get("https://pm25.lass-net.org/API-1.0.0/project/airbox/latest/", timeout=15)
feeds = r.json().get("feeds", [])
print(f"Total feeds: {len(feeds)}")

# 統計時間戳分布
now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
ages = []
no_ts = 0
for f in feeds:
    ts = f.get("timestamp", "")
    if ts:
        try:
            dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            age_h = (now - dt).total_seconds() / 3600
            ages.append(age_h)
        except:
            no_ts += 1
    else:
        no_ts += 1

if ages:
    import statistics
    ages.sort()
    print(f"Age stats (hours): min={ages[0]:.1f}, max={ages[-1]:.1f}, median={statistics.median(ages):.1f}")
    print(f"Within 6h: {sum(1 for a in ages if a <= 6)}")
    print(f"Within 24h: {sum(1 for a in ages if a <= 24)}")
    print(f"Within 7days: {sum(1 for a in ages if a <= 168)}")
    print(f"No timestamp: {no_ts}")
    print(f"Oldest 3 timestamps:")
    for f in feeds[-3:]:
        print(" ", f.get("timestamp"), f.get("area"))
    print(f"Newest 3 timestamps:")
    for f in feeds[:3]:
        print(" ", f.get("timestamp"), f.get("area"))
