import duckdb
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"

def parse_sector_splits():
    con = duckdb.connect(DB_PATH)
    
    df = con.execute("""
        SELECT 
            Driver,
            LapNumber,
            LapTime,
            Sector1Time,
            Sector2Time,
            Sector3Time,
            Compound,
            TyreLife,
            Stint
        FROM laps
        WHERE Sector1Time IS NOT NULL 
          AND Sector2Time IS NOT NULL 
          AND Sector3Time IS NOT NULL
        ORDER BY Driver, LapNumber
    """).df()
    
    con.close()
    return df

def timedelta_str_to_seconds(td_str):
    if pd.isna(td_str):
        return None
    try:
        td = pd.to_timedelta(td_str)
        return td.total_seconds()
    except:
        return None

if __name__ == "__main__":
    df = parse_sector_splits()
    
    for col in ["LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]:
        df[f"{col}_sec"] = df[col].apply(timedelta_str_to_seconds)
    
    print(f"Sector splits for {len(df)} laps")
    print(df[["Driver", "LapNumber", "LapTime_sec", "Sector1Time_sec", "Sector2Time_sec", "Sector3Time_sec"]].head(10).to_string())
    
    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE sector_splits AS SELECT * FROM df")
    con.close()
    print("Saved sector_splits table to DuckDB")