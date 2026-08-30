import duckdb
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"

def optimize_pit_strategy():
    con = duckdb.connect(DB_PATH)
    df = con.execute("SELECT * FROM monte_carlo_results ORDER BY mean_total_time").df()
    con.close()

    best_overall = df.iloc[0]

    best_per_pair = df.loc[df.groupby(["compound_1", "compound_2"])["mean_total_time"].idxmin()]
    best_per_pair = best_per_pair.sort_values("mean_total_time")

    return best_overall, best_per_pair, df

if __name__ == "__main__":
    best_overall, best_per_pair, full_df = optimize_pit_strategy()

    print("=" * 55)
    print("PIT STOP OPTIMIZER — Bahrain 2024 Race")
    print("=" * 55)

    print(f"\nOptimal strategy overall:")
    print(f"  Pit lap {int(best_overall['pit_lap'])}: {best_overall['compound_1']} -> {best_overall['compound_2']}")
    print(f"  Predicted race time: {best_overall['mean_total_time']:.2f}s")
    print(f"  Range (p10-p90): {best_overall['p10']:.2f}s - {best_overall['p90']:.2f}s")

    print(f"\nBest pit lap per compound strategy:")
    for _, row in best_per_pair.iterrows():
        gap_to_best = row["mean_total_time"] - best_overall["mean_total_time"]
        print(f"  {row['compound_1']} -> {row['compound_2']}: pit lap {int(row['pit_lap'])}, "
              f"{row['mean_total_time']:.2f}s (+{gap_to_best:.2f}s vs optimal)")

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE pit_optimizer_recommendations AS SELECT * FROM best_per_pair")
    con.close()
    print("\nSaved pit_optimizer_recommendations table to DuckDB")