import duckdb
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"

def driver_comparison_all():
    con = duckdb.connect(DB_PATH)
    df = con.execute("""
        SELECT Driver, Race, Year, LapNumber, LapTime_sec, Sector1Time_sec, Sector2Time_sec, Sector3Time_sec, Compound, Stint
        FROM sector_splits_multi_year
        WHERE LapTime_sec IS NOT NULL
        ORDER BY Year, Race, Driver, LapNumber
    """).df()
    con.close()

    summary = df.groupby(["Year", "Race", "Driver"]).agg(
        laps=("LapNumber", "count"),
        avg_lap=("LapTime_sec", "mean"),
        best_lap=("LapTime_sec", "min"),
        std_lap=("LapTime_sec", "std"),
    ).round(3).reset_index()

    summary["rank"] = summary.groupby(["Year", "Race"])["best_lap"].rank(method="min").astype(int)
    summary = summary.sort_values(["Year", "Race", "rank"]).reset_index(drop=True)

    return summary, df

if __name__ == "__main__":
    summary, df = driver_comparison_all()
    print(f"Driver comparison, {summary['Year'].nunique()} years, {summary['Race'].nunique()} races, {summary['Driver'].nunique()} drivers")

    print(f"\nFastest driver per race/year:")
    fastest = summary[summary["rank"] == 1][["Year", "Race", "Driver", "best_lap"]]
    print(fastest.sort_values(["Race", "Year"]).to_string(index=False))

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE driver_comparison_multi_year AS SELECT * FROM summary")
    con.close()
    print("\nSaved driver_comparison_multi_year table to DuckDB")