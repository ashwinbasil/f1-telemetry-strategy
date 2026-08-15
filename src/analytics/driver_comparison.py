import duckdb
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"

def driver_comparison(driver_a="VER", driver_b="LEC"):
    con = duckdb.connect(DB_PATH)
    df = con.execute(f"""
        SELECT Driver, LapNumber, LapTime_sec, Sector1Time_sec, Sector2Time_sec, Sector3Time_sec, Compound, Stint
        FROM sector_splits
        WHERE Driver IN ('{driver_a}', '{driver_b}')
          AND LapTime_sec IS NOT NULL
        ORDER BY Driver, LapNumber
    """).df()
    con.close()

    summary = df.groupby("Driver").agg(
        laps=("LapNumber", "count"),
        avg_lap=("LapTime_sec", "mean"),
        best_lap=("LapTime_sec", "min"),
        std_lap=("LapTime_sec", "std"),
        avg_s1=("Sector1Time_sec", "mean"),
        avg_s2=("Sector2Time_sec", "mean"),
        avg_s3=("Sector3Time_sec", "mean"),
    ).round(3).reset_index()

    return summary, df

if __name__ == "__main__":
    summary, df = driver_comparison()
    print("Driver comparison summary:")
    print(summary.to_string(index=False))
    print(f"\nLower std_lap = more consistent pace across stint")

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE driver_comparison AS SELECT * FROM summary")
    con.close()
    print("\nSaved driver_comparison table to DuckDB")