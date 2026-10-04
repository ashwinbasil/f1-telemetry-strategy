import duckdb
import numpy as np
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"
LAP_TIME_NOISE_STD = 0.3
FALLBACK_PIT_LOSS = 22.0
MIN_CLIFF_STINTS = 2

def get_pit_loss(race):
    con = duckdb.connect(DB_PATH)
    result = con.execute(f"SELECT pit_loss_estimate_sec FROM pit_loss_estimates WHERE Race = '{race}'").fetchone()
    con.close()
    return result[0] if result else FALLBACK_PIT_LOSS

def get_race_lap_count(year, race):
    con = duckdb.connect(DB_PATH)
    result = con.execute(f"SELECT MAX(LapNumber) FROM laps_multi_year WHERE Race = '{race}' AND Year = {year}").fetchone()
    con.close()
    return int(result[0])

def get_deg_params(year, race, compound):
    con = duckdb.connect(DB_PATH)
    df = con.execute(f"""
        SELECT AVG(deg_rate_sec_per_lap) as avg_deg, AVG(base_laptime_normalized) as avg_base
        FROM tire_degradation_multi_year
        WHERE Race = '{race}' AND Year = {year} AND Compound = '{compound}'
    """).df()
    con.close()
    if df["avg_deg"].isna().iloc[0]:
        return None, None
    return df["avg_deg"].iloc[0], df["avg_base"].iloc[0]

def get_cliff_params(year, race, compound):
    con = duckdb.connect(DB_PATH)
    df = con.execute(f"""
        SELECT avg_cliff_age, avg_slope_before, avg_slope_after, n_stints
        FROM cliff_params
        WHERE Race = '{race}' AND Year = {year} AND Compound = '{compound}'
    """).df()
    con.close()
    if len(df) == 0 or df["n_stints"].iloc[0] < MIN_CLIFF_STINTS:
        return None
    return df.iloc[0].to_dict()

def simulate_stint_laps(laps_in_stint, base, linear_deg, cliff):
    laps = np.arange(1, laps_in_stint + 1)
    if cliff is None:
        times = base + linear_deg * laps
    else:
        cliff_age = cliff["avg_cliff_age"]
        slope_before = cliff["avg_slope_before"]
        slope_after = cliff["avg_slope_after"]
        times = np.where(
            laps <= cliff_age,
            base + slope_before * laps,
            base + slope_before * cliff_age + slope_after * (laps - cliff_age)
        )
    return times + np.random.normal(0, LAP_TIME_NOISE_STD, len(laps))

def simulate_one_stop(year, race, total_laps, pit_lap, compound_1, compound_2, n_trials=1000):
    deg1, base1 = get_deg_params(year, race, compound_1)
    deg2, base2 = get_deg_params(year, race, compound_2)
    if deg1 is None or deg2 is None:
        return None

    cliff1 = get_cliff_params(year, race, compound_1)
    cliff2 = get_cliff_params(year, race, compound_2)
    pit_loss = get_pit_loss(race)

    results = []
    for _ in range(n_trials):
        stint1_times = simulate_stint_laps(pit_lap, base1, deg1, cliff1)
        stint2_times = simulate_stint_laps(total_laps - pit_lap, base2, deg2, cliff2)
        total_time = stint1_times.sum() + stint2_times.sum() + pit_loss
        results.append(total_time)

    return np.array(results), (cliff1 is not None or cliff2 is not None)

def run_all_years_races():
    con = duckdb.connect(DB_PATH)
    year_race_pairs = con.execute("SELECT DISTINCT Year, Race FROM tire_degradation_multi_year").df()
    con.close()

    all_results = []
    for _, row in year_race_pairs.iterrows():
        year, race = row["Year"], row["Race"]
        total_laps = get_race_lap_count(year, race)
        pit_loss = get_pit_loss(race)
        pit_lap_options = [int(total_laps * f) for f in [0.3, 0.4, 0.5, 0.6, 0.7]]

        con = duckdb.connect(DB_PATH)
        compounds = con.execute(f"""
            SELECT DISTINCT Compound FROM tire_degradation_multi_year
            WHERE Year = {year} AND Race = '{race}'
        """).df()["Compound"].tolist()
        con.close()

        cliff_scenarios = 0
        for pit_lap in pit_lap_options:
            for c1 in compounds:
                for c2 in compounds:
                    result = simulate_one_stop(year, race, total_laps, pit_lap, c1, c2, n_trials=1000)
                    if result is None:
                        continue
                    trials, used_cliff = result
                    if used_cliff:
                        cliff_scenarios += 1
                    all_results.append({
                        "Year": year, "Race": race, "total_laps": total_laps,
                        "pit_loss_used": round(pit_loss, 2), "pit_lap": pit_lap,
                        "compound_1": c1, "compound_2": c2,
                        "used_cliff_model": used_cliff,
                        "mean_total_time": round(trials.mean(), 2),
                        "std_total_time": round(trials.std(), 2),
                        "p10": round(np.percentile(trials, 10), 2),
                        "p90": round(np.percentile(trials, 90), 2)
                    })
        print(f"{year} {race}: {total_laps} laps, pit loss {pit_loss:.2f}s, {cliff_scenarios} scenarios used cliff model, done")

    return pd.DataFrame(all_results)

if __name__ == "__main__":
    summary_df = run_all_years_races()
    print(f"\nTotal scenarios: {len(summary_df)}, {summary_df['used_cliff_model'].sum()} used piecewise cliff model")

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE monte_carlo_multi_year AS SELECT * FROM summary_df")
    con.close()
    print("Saved monte_carlo_multi_year table to DuckDB")