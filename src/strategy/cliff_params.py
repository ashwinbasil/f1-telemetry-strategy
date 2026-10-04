import duckdb
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"

def aggregate_cliff_params():
    con = duckdb.connect(DB_PATH)
    df = con.execute("""
        SELECT Year, Race, Compound, cliff_tyre_age, slope_before_cliff, slope_after_cliff
        FROM tire_cliff_analysis
        WHERE cliff_detected = true
    """).df()
    con.close()

    agg = df.groupby(["Year", "Race", "Compound"]).agg(
        avg_cliff_age=("cliff_tyre_age", "mean"),
        avg_slope_before=("slope_before_cliff", "mean"),
        avg_slope_after=("slope_after_cliff", "mean"),
        n_stints=("cliff_tyre_age", "count")
    ).round(3).reset_index()

    return agg

if __name__ == "__main__":
    agg = aggregate_cliff_params()
    print(f"Cliff parameters aggregated across {len(agg)} (year, race, compound) groups:")
    print(agg.to_string(index=False))

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE cliff_params AS SELECT * FROM agg")
    con.close()
    print("\nSaved cliff_params table to DuckDB")