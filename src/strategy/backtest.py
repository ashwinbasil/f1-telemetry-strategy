import duckdb
import pandas as pd
import numpy as np

DB_PATH = "/app/data/processed/telemetry.duckdb"

def time_to_seconds(t):
    try:
        return pd.to_timedelta(t).total_seconds()
    except:
        return None

def get_actual_winner(race, year):
    con = duckdb.connect(DB_PATH)
    winner_row = con.execute(f"""
        SELECT Driver FROM race_results
        WHERE Race = '{race}' AND Year = {year} AND Position = 1
    """).df()
    con.close()
    if len(winner_row) == 0:
        return None
    return winner_row["Driver"].iloc[0]

def get_winner_strategy_and_time(driver, race, year):
    con = duckdb.connect(DB_PATH)
    laps = con.execute(f"""
        SELECT LapNumber, LapTime, Compound, Stint
        FROM laps_multi_year
        WHERE Race = '{race}' AND Year = {year} AND Driver = '{driver}' AND LapTime IS NOT NULL
        ORDER BY LapNumber
    """).df()
    con.close()

    laps["LapTime_sec"] = laps["LapTime"].apply(time_to_seconds)
    laps = laps.dropna(subset=["LapTime_sec"])
    if len(laps) == 0:
        return None

    total_time = laps["LapTime_sec"].sum()
    stints = laps.groupby("Stint").agg(compound=("Compound", "first"), laps=("LapNumber", "count")).reset_index()

    return {
        "actual_total_time": total_time,
        "n_stops": len(stints) - 1,
        "strategy": stints.to_dict("records")
    }

def run_backtest():
    con = duckdb.connect(DB_PATH)
    year_race_pairs = con.execute("SELECT DISTINCT Year, Race FROM pit_optimizer_multi_year").df()
    optimizer_results = con.execute("SELECT * FROM pit_optimizer_multi_year").df()
    con.close()

    results = []
    for _, row in year_race_pairs.iterrows():
        year, race = row["Year"], row["Race"]
        winner = get_actual_winner(race, year)
        if winner is None:
            print(f"  {year} {race}: no winner found in race_results, skipping")
            continue

        actual = get_winner_strategy_and_time(winner, race, year)
        if actual is None:
            continue

        predicted = optimizer_results[(optimizer_results["Year"] == year) & (optimizer_results["Race"] == race)]
        if len(predicted) == 0:
            continue
        predicted = predicted.iloc[0]

        gap_sec = actual["actual_total_time"] - predicted["mean_total_time"]
        gap_pct = (gap_sec / actual["actual_total_time"]) * 100

        actual_compounds = " -> ".join([s["compound"] for s in actual["strategy"] if pd.notna(s["compound"])])
        predicted_compounds = f"{predicted['compound_1']} -> {predicted['compound_2']}"
        stop_count_match = actual["n_stops"] == 1
        compound_match = stop_count_match and set(actual_compounds.split(" -> ")) == set([predicted["compound_1"], predicted["compound_2"]])

        results.append({
            "Year": year, "Race": race, "actual_winner": winner,
            "actual_n_stops": actual["n_stops"], "actual_strategy": actual_compounds,
            "actual_total_time": round(actual["actual_total_time"], 2),
            "predicted_strategy": predicted_compounds,
            "predicted_total_time": predicted["mean_total_time"],
            "gap_sec": round(gap_sec, 2), "gap_pct": round(gap_pct, 2),
            "stop_count_match": stop_count_match, "compound_match": compound_match
        })

    return pd.DataFrame(results)

if __name__ == "__main__":
    results = run_backtest()
    print(f"Backtest: model prediction vs actual race winner, {len(results)} races")
    print(results[["Year", "Race", "actual_winner", "actual_strategy", "predicted_strategy", "gap_pct", "stop_count_match", "compound_match"]].to_string(index=False))

    print(f"\nMean |gap|: {results['gap_pct'].abs().mean():.2f}%")
    print(f"Stop count match: {results['stop_count_match'].sum()} of {len(results)}")
    print(f"Compound exact match: {results['compound_match'].sum()} of {len(results)}")

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE backtest_results AS SELECT * FROM results")
    con.close()
    print("\nSaved backtest_results table to DuckDB")