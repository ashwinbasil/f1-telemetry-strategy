import duckdb
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"

def timedelta_str_to_seconds(td_str):
    if pd.isna(td_str):
        return None
    try:
        td = pd.to_timedelta(td_str)
        return td.total_seconds()
    except:
        return None

def parse_sector_splits():
    con = duckdb.connect(DB_PATH)
    df = con.execute("""
        SELECT Driver, Race, Year, LapNumber, LapTime, Sector1Time, Sector2Time, Sector3Time,
               Compound, TyreLife, Stint, TrackStatus
        FROM laps_multi_race
        WHERE Sector1Time IS NOT NULL
          AND Sector2Time IS NOT NULL
          AND Sector3Time IS NOT NULL
    """).df()
    con.close()

    for col in ["LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]:
        df[f"{col}_sec"] = df[col].apply(timedelta_str_to_seconds)

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE sector_splits_multi_race AS SELECT * FROM df")
    result = con.execute("SELECT COUNT(*) FROM sector_splits_multi_race").fetchone()
    races = con.execute("SELECT COUNT(DISTINCT Race) FROM sector_splits_multi_race").fetchone()
    con.close()
    print(f"sector_splits_multi_race: {result[0]} laps, {races[0]} races")

if __name__ == "__main__":
    parse_sector_splits()
