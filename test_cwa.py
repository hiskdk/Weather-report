import requests
import json

API_KEY = "CWA-55FDA6D3-A43C-4AE0-BB30-E62D5F684FB2"

def test_obs():
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization={API_KEY}&limit=5"
    r = requests.get(url, timeout=10)
    print("O-A0003-001 Status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        stations = data.get("records", {}).get("Station", [])
        print(f"Station count: {len(stations)}")
        if stations:
            s = stations[0]
            print("Station Name:", s.get("StationName"))
            print("Station ID:", s.get("StationId"))
            print("County:", s.get("GeoInfo", {}).get("CountyName"))
            print("Town:", s.get("GeoInfo", {}).get("TownName"))
            coords = s.get("GeoInfo", {}).get("Coordinates", [])
            print("Coords:", coords)
            elem = s.get("WeatherElement", {})
            print("AirTemperature:", elem.get("AirTemperature"))
            print("Weather:", elem.get("Weather"))
            print("DailyExtreme:", elem.get("DailyExtreme"))

if __name__ == "__main__":
    test_obs()
