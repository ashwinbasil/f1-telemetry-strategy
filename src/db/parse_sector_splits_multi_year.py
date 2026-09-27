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

def parse_sector_splits():
    con = duckdb.connect(DB_PATH)
    df = con.execute("""
        SELECT Driver, Race, Year, LapNumber, LapTime, Sector1Time, Sector2Time, Sector3Time,
               Compound, TyreLife, Stint, TrackStatus, PitInTime, PitOutTime
        FROM laps_multi_year
        WHERE Sector1Time IS NOT NULL
          AND Sector2Time IS NOT NULL
          AND Sector3Time IS NOT NULL
    """).df()
    con.close()

    for col in ["LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]:
        df[f"{col}_sec"] = df[col].apply(time_to_seconds)

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE sector_splits_multi_year AS SELECT * FROM df")
    result = con.execute("SELECT COUNT(*) FROM sector_splits_multi_year").fetchone()
    years = con.execute("SELECT COUNT(DISTINCT Year) FROM sector_splits_multi_year").fetchone()
    con.close()
    print(f"sector_splits_multi_year: {result[0]} laps, {years[0]} years")

if __name__ == "__main__":
    parse_sector_splits()