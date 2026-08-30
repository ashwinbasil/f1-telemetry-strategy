import duckdb
import numpy as np
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"
PIT_LOSS_SEC = 22.0
TOTAL_LAPS = 56
LAP_TIME_NOISE_STD = 0.3

def get_deg_params(compound):
    con = duckdb.connect(DB_PATH)
    df = con.execute(f"""
        SELECT AVG(deg_rate_sec_per_lap) as avg_deg, AVG(base_laptime_normalized) as avg_base
        FROM tire_degradation
        WHERE Compound = '{compound}'
    """).df()
    con.close()
    return df["avg_deg"].iloc[0], df["avg_base"].iloc[0]

def simulate_one_stop(pit_lap, compound_1, compound_2, n_trials=1000):
    deg1, base1 = get_deg_params(compound_1)
    deg2, base2 = get_deg_params(compound_2)

    results = []
    for _ in range(n_trials):
        stint1_laps = np.arange(1, pit_lap + 1)
        stint1_times = base1 + deg1 * stint1_laps + np.random.normal(0, LAP_TIME_NOISE_STD, len(stint1_laps))

        stint2_laps = np.arange(1, TOTAL_LAPS - pit_lap + 1)
        stint2_times = base2 + deg2 * stint2_laps + np.random.normal(0, LAP_TIME_NOISE_STD, len(stint2_laps))

        total_time = stint1_times.sum() + stint2_times.sum() + PIT_LOSS_SEC
        results.append(total_time)

    return np.array(results)

if __name__ == "__main__":
    pit_lap_options = [15, 20, 25, 30, 35]
    compound_pairs = [("SOFT", "HARD"), ("HARD", "SOFT"), ("HARD", "HARD"), ("SOFT", "SOFT")]

    summary = []
    for pit_lap in pit_lap_options:
        for c1, c2 in compound_pairs:
            trials = simulate_one_stop(pit_lap, c1, c2, n_trials=1000)
            summary.append({
                "pit_lap": pit_lap,
                "compound_1": c1,
                "compound_2": c2,
                "mean_total_time": round(trials.mean(), 2),
                "std_total_time": round(trials.std(), 2),
                "p10": round(np.percentile(trials, 10), 2),
                "p90": round(np.percentile(trials, 90), 2)
            })

    summary_df = pd.DataFrame(summary)
    summary_df = summary_df.sort_values("mean_total_time")
    print("Monte Carlo pit strategy results (1000 trials each, normalized base laptime):")
    print(summary_df.to_string(index=False))

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE monte_carlo_results AS SELECT * FROM summary_df")
    con.close()
    print("\nSaved monte_carlo_results table to DuckDB")