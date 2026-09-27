import duckdb
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"

def optimize_all_years_races():
    con = duckdb.connect(DB_PATH)
    df = con.execute("SELECT * FROM monte_carlo_multi_year").df()
    con.close()

    best = df.loc[df.groupby(["Year", "Race"])["mean_total_time"].idxmin()]
    best = best.sort_values(["Race", "Year"]).reset_index(drop=True)

    return best, df

if __name__ == "__main__":
    best, full_df = optimize_all_years_races()

    print("=" * 60)
    print("PIT STOP OPTIMIZER — Best strategy per race, per year")
    print("=" * 60)
    for _, row in best.iterrows():
        print(f"\n{row['Race']} {int(row['Year'])} ({int(row['total_laps'])} laps):")
        print(f"  Pit lap {int(row['pit_lap'])}: {row['compound_1']} -> {row['compound_2']}")
        print(f"  Predicted race time: {row['mean_total_time']:.2f}s")

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE pit_optimizer_multi_year AS SELECT * FROM best")
    con.close()
    print("\nSaved pit_optimizer_multi_year table to DuckDB")