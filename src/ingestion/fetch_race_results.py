import fastf1
import os
import pandas as pd
import duckdb

CACHE_DIR = os.environ.get("FASTF1_CACHE", "/app/data/raw/fastf1_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

DB_PATH = "/app/data/processed/telemetry.duckdb"

ALL_RACES = [
    (2023, "Bahrain"), (2023, "Saudi Arabia"), (2023, "Australia"),
    (2023, "Monaco"),  (2023, "Singapore"),    (2023, "Belgium"),
    (2023, "Japan"),   (2023, "Monza"),
    (2024, "Bahrain"), (2024, "Saudi Arabia"), (2024, "Australia"),
    (2024, "Monaco"),  (2024, "Singapore"),    (2024, "Belgium"),
    (2024, "Japan"),   (2024, "Monza"),
]

def derive_winner_from_laps(session, gp, year):
    """When session.results is empty (Ergast unavailable), derive finishing order
    from total race time, filtering to drivers who completed the full race distance."""
    laps = session.laps
    if laps is None or len(laps) == 0:
        return None

    lap_counts = laps.groupby("Driver")["LapNumber"].count()
    max_laps = lap_counts.max()
    finishers = lap_counts[lap_counts >= max_laps - 1].index

    totals = laps[laps["Driver"].isin(finishers)].groupby("Driver")["LapTime"].sum()
    totals = totals.dropna().sort_values()

    ranking = pd.DataFrame({
        "Driver": totals.index,
        "Position": range(1, len(totals) + 1),
        "TeamName": None,
        "Race": gp,
        "Year": year
    })
    return ranking

def fetch_all_results(races):
    all_results = []
    for year, gp in races:
        print(f"Fetching results: {year} {gp}...")
        try:
            session = fastf1.get_session(year, gp, "R")
            session.load(telemetry=False, weather=False, messages=False)

            results = session.results
            if results is not None and len(results) > 0 and "Position" in results.columns:
                results = results[["Abbreviation", "Position", "TeamName"]].copy()
                results = results.rename(columns={"Abbreviation": "Driver"})
                results["Race"] = gp
                results["Year"] = year
                results["Position"] = pd.to_numeric(results["Position"], errors="coerce")
                results = results.dropna(subset=["Position"])
            else:
                results = None

            if results is None or len(results) == 0:
                print(f"  Official results unavailable (Ergast), deriving from lap times instead")
                results = derive_winner_from_laps(session, gp, year)

            if results is None or len(results) == 0:
                print(f"  FAILED: could not derive results for {gp} {year}")
                continue

            winner = results[results["Position"] == 1]["Driver"].values
            print(f"  Winner: {winner[0] if len(winner) > 0 else 'NOT FOUND'}")
            all_results.append(results)
        except Exception as e:
            print(f"  FAILED {year} {gp}: {e}")

    if not all_results:
        return pd.DataFrame()
    return pd.concat(all_results, ignore_index=True)

if __name__ == "__main__":
    combined = fetch_all_results(ALL_RACES)
    con = duckdb.connect(DB_PATH)
    con.register("results_df", combined)
    con.execute("CREATE OR REPLACE TABLE race_results AS SELECT * FROM results_df")
    con.close()
    print(f"\nSaved race_results: {len(combined)} rows across {combined['Race'].nunique()} races")
    print("\nWinners stored:")
    print(combined[combined["Position"] == 1][["Year", "Race", "Driver"]].to_string(index=False))