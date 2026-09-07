import duckdb
import numpy as np
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"
PIT_LOSS_SEC = 22.0
LAP_TIME_NOISE_STD = 0.3

def get_race_lap_count(race):
    con = duckdb.connect(DB_PATH)
    result = con.execute(f"SELECT MAX(LapNumber) FROM laps_multi_race WHERE Race = '{race}'").fetchone()
    con.close()
    return int(result[0])

def get_deg_params(race, compound):
    con = duckdb.connect(DB_PATH)
    df = con.execute(f"""
        SELECT AVG(deg_rate_sec_per_lap) as avg_deg, AVG(base_laptime_normalized) as avg_base
        FROM tire_degradation_multi_race
        WHERE Race = '{race}' AND Compound = '{compound}'
    """).df()
    con.close()
    if df["avg_deg"].isna().iloc[0]:
        return None, None
    return df["avg_deg"].iloc[0], df["avg_base"].iloc[0]

def simulate_one_stop(race, total_laps, pit_lap, compound_1, compound_2, n_trials=1000):
    deg1, base1 = get_deg_params(race, compound_1)
    deg2, base2 = get_deg_params(race, compound_2)
    if deg1 is None or deg2 is None:
        return None

    results = []
    for _ in range(n_trials):
        stint1_laps = np.arange(1, pit_lap + 1)
        stint1_times = base1 + deg1 * stint1_laps + np.random.normal(0, LAP_TIME_NOISE_STD, len(stint1_laps))

        stint2_laps = np.arange(1, total_laps - pit_lap + 1)
        stint2_times = base2 + deg2 * stint2_laps + np.random.normal(0, LAP_TIME_NOISE_STD, len(stint2_laps))

        total_time = stint1_times.sum() + stint2_times.sum() + PIT_LOSS_SEC
        results.append(total_time)

    return np.array(results)

def run_all_races():
    con = duckdb.connect(DB_PATH)
    races = con.execute("SELECT DISTINCT Race FROM tire_degradation_multi_race").df()["Race"].tolist()
    compounds_per_race = con.execute("SELECT Race, Compound FROM tire_degradation_multi_race GROUP BY Race, Compound").df()
    con.close()

    all_results = []
    for race in races:
        total_laps = get_race_lap_count(race)
        pit_lap_options = [int(total_laps * f) for f in [0.3, 0.4, 0.5, 0.6, 0.7]]
        compounds = compounds_per_race[compounds_per_race["Race"] == race]["Compound"].tolist()

        for pit_lap in pit_lap_options:
            for c1 in compounds:
                for c2 in compounds:
                    trials = simulate_one_stop(race, total_laps, pit_lap, c1, c2, n_trials=1000)
                    if trials is None:
                        continue
                    all_results.append({
                        "Race": race,
                        "total_laps": total_laps,
                        "pit_lap": pit_lap,
                        "compound_1": c1,
                        "compound_2": c2,
                        "mean_total_time": round(trials.mean(), 2),
                        "std_total_time": round(trials.std(), 2),
                        "p10": round(np.percentile(trials, 10), 2),
                        "p90": round(np.percentile(trials, 90), 2)
                    })
        print(f"{race}: {total_laps} laps, done")

    return pd.DataFrame(all_results)

if __name__ == "__main__":
    summary_df = run_all_races()
    print(f"\nTotal scenarios: {len(summary_df)}")

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE monte_carlo_multi_race AS SELECT * FROM summary_df")
    con.close()
    print("Saved monte_carlo_multi_race table to DuckDB")