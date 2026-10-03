import sqlite3
con = sqlite3.connect('data.db')
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', tables)
for t in tables:
    cur.execute(f'SELECT COUNT(*) FROM "{t}"')
    cnt = cur.fetchone()[0]
    print(f'  {t}: {cnt} rows')
    if cnt > 0 and t == 'StationObservations':
        cur.execute(f'SELECT station_name, temperature, humidity, wind_speed, precipitation FROM "{t}" LIMIT 3')
        for row in cur.fetchall():
            print('   Sample:', row)
con.close()
