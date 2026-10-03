"""
database.py
SQLite 資料庫管理模組
符合課程作業步驟 8, 9, 10, 12, 20 要求，並擴充支援全維度即時氣象觀測儲存。
"""

import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional

DB_FILE = "data.db"

def get_connection(db_file: str = DB_FILE) -> sqlite3.Connection:
    """取得 SQLite 資料庫連線"""
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_file: str = DB_FILE):
    """
    初始化資料表 (步驟 8、9、20)
    建立 TemperatureForecasts 與 StationObservations 資料表
    """
    with get_connection(db_file) as conn:
        cursor = conn.cursor()
        
        # 1. 氣溫預報資料表 (符合作業第 9 步規格)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS TemperatureForecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regionName TEXT NOT NULL,
            dataDate TEXT NOT NULL,
            minT REAL NOT NULL,
            maxT REAL NOT NULL,
            weather TEXT DEFAULT '晴時多雲',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(regionName, dataDate) ON CONFLICT REPLACE
        )
        """)

        # 檢查 StationObservations 是否有 air_pressure 欄位，若舊表結構不符合則升級
        cursor.execute("PRAGMA table_info(StationObservations);")
        columns = [row[1] for row in cursor.fetchall()]
        if columns and "air_pressure" not in columns:
            cursor.execute("DROP TABLE StationObservations;")

        # 2. 測站全維度即時觀測資料表 (儲存 O-A0003-001)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS StationObservations (
            station_id TEXT PRIMARY KEY,
            station_name TEXT NOT NULL,
            county TEXT NOT NULL,
            town TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            temperature REAL,
            humidity REAL,
            air_pressure REAL,
            wind_speed REAL,
            wind_direction REAL,
            gust_speed REAL,
            precipitation REAL,
            weather TEXT,
            daily_high REAL,
            daily_low REAL,
            obs_time TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
    print("SQLite 資料庫與資料表初始化完成！")

def insert_forecasts(records: List[Dict[str, Any]], db_file: str = DB_FILE) -> int:
    """插入預報資料 (重複自動更新)"""
    if not records:
        return 0
    with get_connection(db_file) as conn:
        cursor = conn.cursor()
        cursor.executemany("""
        INSERT INTO TemperatureForecasts (regionName, dataDate, minT, maxT, weather)
        VALUES (:regionName, :dataDate, :minT, :maxT, :weather)
        ON CONFLICT(regionName, dataDate) DO UPDATE SET
            minT=excluded.minT,
            maxT=excluded.maxT,
            weather=excluded.weather,
            created_at=CURRENT_TIMESTAMP
        """, records)
        conn.commit()
        return len(records)

def insert_observations(stations: List[Dict[str, Any]], db_file: str = DB_FILE) -> int:
    """插入/更新即時測站觀測資料 (O-A0003-001)"""
    if not stations:
        return 0
    with get_connection(db_file) as conn:
        cursor = conn.cursor()
        cursor.executemany("""
        INSERT INTO StationObservations (
            station_id, station_name, county, town,
            latitude, longitude, temperature, humidity,
            air_pressure, wind_speed, wind_direction, gust_speed,
            precipitation, weather, daily_high, daily_low, obs_time
        ) VALUES (
            :station_id, :station_name, :county, :town,
            :latitude, :longitude, :temperature, :humidity,
            :air_pressure, :wind_speed, :wind_direction, :gust_speed,
            :precipitation, :weather, :daily_high, :daily_low, :obs_time
        ) ON CONFLICT(station_id) DO UPDATE SET
            station_name=excluded.station_name,
            county=excluded.county,
            town=excluded.town,
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            temperature=excluded.temperature,
            humidity=excluded.humidity,
            air_pressure=excluded.air_pressure,
            wind_speed=excluded.wind_speed,
            wind_direction=excluded.wind_direction,
            gust_speed=excluded.gust_speed,
            precipitation=excluded.precipitation,
            weather=excluded.weather,
            daily_high=excluded.daily_high,
            daily_low=excluded.daily_low,
            obs_time=excluded.obs_time,
            updated_at=CURRENT_TIMESTAMP
        """, stations)
        conn.commit()
        return len(stations)

def get_distinct_regions(db_file: str = DB_FILE) -> List[str]:
    """查詢所有地區清單 (步驟 10)"""
    with get_connection(db_file) as conn:
        df = pd.read_sql_query("SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY regionName;", conn)
        return df["regionName"].tolist()

def get_forecasts_by_region(region_name: str, db_file: str = DB_FILE) -> pd.DataFrame:
    """查詢特定地區的一週預報 (步驟 10、12)"""
    with get_connection(db_file) as conn:
        query = "SELECT dataDate, minT, maxT, weather FROM TemperatureForecasts WHERE regionName = ? ORDER BY dataDate ASC;"
        df = pd.read_sql_query(query, conn, params=(region_name,))
        return df

def get_all_forecasts_dict(db_file: str = DB_FILE) -> Dict[str, List[Dict[str, Any]]]:
    """查詢所有地區一週氣溫預報，轉為前端即時字典 (步驟 13-16)"""
    with get_connection(db_file) as conn:
        df = pd.read_sql_query("SELECT regionName, dataDate, minT, maxT, weather FROM TemperatureForecasts ORDER BY regionName, dataDate ASC;", conn)
        if df.empty:
            return {}
        result = {}
        for reg, group in df.groupby("regionName"):
            result[reg] = group[["dataDate", "minT", "maxT", "weather"]].to_dict(orient="records")
        return result

def get_all_stations(county: Optional[str] = None, db_file: str = DB_FILE) -> pd.DataFrame:
    """查詢全台即時測站資料"""
    with get_connection(db_file) as conn:
        if county and county != "全部縣市":
            query = "SELECT * FROM StationObservations WHERE county = ? ORDER BY temperature DESC;"
            df = pd.read_sql_query(query, conn, params=(county,))
        else:
            query = "SELECT * FROM StationObservations ORDER BY temperature DESC;"
            df = pd.read_sql_query(query, conn)
        return df

def get_weather_summary(db_file: str = DB_FILE) -> Dict[str, Any]:
    """
    計算四宮格核心極值：
    - 最高溫 (溫度, 測站名)
    - 最低溫 (溫度, 測站名)
    - 最大雨量 (雨量, 測站名)
    - 最大風速 (風速, 測站名)
    - 測站總數、最新觀測時間
    """
    with get_connection(db_file) as conn:
        df = pd.read_sql_query("SELECT * FROM StationObservations WHERE temperature IS NOT NULL AND temperature > -50;", conn)
        if df.empty:
            return {
                "station_count": 0,
                "obs_time": "--",
                "max_temp": {"val": 0.0, "station": "無資料", "county": ""},
                "min_temp": {"val": 0.0, "station": "無資料", "county": ""},
                "max_rain": {"val": 0.0, "station": "無資料", "county": ""},
                "max_wind": {"val": 0.0, "station": "無資料", "county": ""},
                "avg_temp": 0.0,
                "max_station": "無資料",
                "min_station": "無資料",
                "updated_at": "--"
            }
        
        # 最高溫與最低溫
        t_sorted = df.sort_values(by="temperature", ascending=False)
        max_t_row = t_sorted.iloc[0]
        min_t_row = t_sorted.iloc[-1]
        
        # 最大雨量
        rain_df = df[df["precipitation"].notnull() & (df["precipitation"] >= 0)].sort_values(by="precipitation", ascending=False)
        max_r_row = rain_df.iloc[0] if not rain_df.empty else max_t_row
        
        # 最大風速
        wind_df = df[df["wind_speed"].notnull() & (df["wind_speed"] >= 0)].sort_values(by="wind_speed", ascending=False)
        max_w_row = wind_df.iloc[0] if not wind_df.empty else max_t_row

        return {
            "station_count": len(df),
            "obs_time": df["obs_time"].max() or "",
            "max_temp": {
                "val": round(float(max_t_row["temperature"]), 1),
                "station": max_t_row["station_name"],
                "county": max_t_row["county"]
            },
            "min_temp": {
                "val": round(float(min_t_row["temperature"]), 1),
                "station": min_t_row["station_name"],
                "county": min_t_row["county"]
            },
            "max_rain": {
                "val": round(float(max_r_row["precipitation"]), 1) if pd.notnull(max_r_row["precipitation"]) else 0.0,
                "station": max_r_row["station_name"],
                "county": max_r_row["county"]
            },
            "max_wind": {
                "val": round(float(max_w_row["wind_speed"]), 1) if pd.notnull(max_w_row["wind_speed"]) else 0.0,
                "station": max_w_row["station_name"],
                "county": max_w_row["county"]
            },
            "avg_temp": round(df["temperature"].mean(), 1),
            "max_station": f"{max_t_row['county']} {max_t_row['station_name']}",
            "min_station": f"{min_t_row['county']} {min_t_row['station_name']}",
            "updated_at": df["obs_time"].max() or ""
        }

get_overall_stats = get_weather_summary
