import duckdb
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"

def time_to_seconds(t):
    if pd.isna(t):
        return None
    try:
        return pd.to_timedelta(t).total_seconds()
    except:
        return None

def load_and_merge():
    con = duckdb.connect(DB_PATH)
    con.execute("""
        CREATE OR REPLACE TABLE weather_multi_year AS
        SELECT * FROM read_csv_auto('/app/data/processed/weather_multi_year.csv')
    """)

    laps = con.execute("SELECT * FROM sector_splits_multi_year").df()
    weather = con.execute("SELECT Time, TrackTemp, AirTemp, Humidity, Rainfall, Race, Year FROM weather_multi_year").df()
    con.close()

    laps = laps.dropna(subset=["LapTime_sec"]).copy()
    weather["Time_sec"] = weather["Time"].apply(time_to_seconds)
    weather = weather.dropna(subset=["Time_sec"])

    merged_all = []
    for (race, year), lap_group in laps.groupby(["Race", "Year"]):
        weather_group = weather[(weather["Race"] == race) & (weather["Year"] == year)].sort_values("Time_sec")
        if len(weather_group) == 0:
            continue

        lap_group = lap_group.sort_values(["Driver", "LapNumber"]).copy()
        lap_group["cum_time_sec"] = lap_group.groupby("Driver")["LapTime_sec"].cumsum()
        lap_group = lap_group.dropna(subset=["cum_time_sec"])

        merged = pd.merge_asof(
            lap_group.sort_values("cum_time_sec"),
            weather_group[["Time_sec", "TrackTemp", "AirTemp", "Humidity", "Rainfall"]].sort_values("Time_sec"),
            left_on="cum_time_sec", right_on="Time_sec", direction="nearest"
        )
        merged_all.append(merged)

    result = pd.concat(merged_all, ignore_index=True)
    return result

if __name__ == "__main__":
    result = load_and_merge()
    print(f"Merged {len(result)} laps with weather data")
    print(f"TrackTemp coverage: {result['TrackTemp'].notna().sum()} of {len(result)} laps have temp data")
    print(result[["Race", "Year", "Driver", "LapNumber", "TrackTemp"]].head(10).to_string(index=False))

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE sector_splits_with_weather AS SELECT * FROM result")
    con.close()
    print("\nSaved sector_splits_with_weather table to DuckDB")