import duckdb
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"

def optimize_all_races():
    con = duckdb.connect(DB_PATH)
    df = con.execute("SELECT * FROM monte_carlo_multi_race").df()
    con.close()

    best_per_race = df.loc[df.groupby("Race")["mean_total_time"].idxmin()]
    best_per_race = best_per_race.sort_values("Race").reset_index(drop=True)

    return best_per_race, df

if __name__ == "__main__":
    best_per_race, full_df = optimize_all_races()

    print("=" * 60)
    print("PIT STOP OPTIMIZER — Best strategy per race, 2024")
    print("=" * 60)
    for _, row in best_per_race.iterrows():
        print(f"\n{row['Race']} ({int(row['total_laps'])} laps):")
        print(f"  Pit lap {int(row['pit_lap'])}: {row['compound_1']} -> {row['compound_2']}")
        print(f"  Predicted race time: {row['mean_total_time']:.2f}s")

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE pit_optimizer_multi_race AS SELECT * FROM best_per_race")
    con.close()
    print("\nSaved pit_optimizer_multi_race table to DuckDB")