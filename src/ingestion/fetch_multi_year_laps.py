import fastf1
import os
import pandas as pd
import duckdb   # ← ADD THIS

CACHE_DIR = os.environ.get("FASTF1_CACHE", "/app/data/raw/fastf1_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

DB_PATH = "/app/data/processed/telemetry.duckdb"   # ← ADD THIS

RACES_2023 = [
    (2023, "Bahrain"),
    (2023, "Saudi Arabia"),
    (2023, "Australia"),
    (2023, "Monaco"),
    (2023, "Singapore"),
    (2023, "Belgium"),
    (2023, "Japan"),
    (2023, "Monza"),
]

# ↓ ADD THIS FUNCTION
def fetch_race_results(session, gp, year):
    """Extract official finishing positions from a loaded FastF1 session."""
    try:
        results = session.results[["Abbreviation", "Position", "TeamName"]].copy()
        results = results.rename(columns={"Abbreviation": "Driver"})
        results["Race"] = gp
        results["Year"] = year
        results["Position"] = pd.to_numeric(results["Position"], errors="coerce")
        return results.dropna(subset=["Position"])
    except Exception as e:
        print(f"  WARNING: Could not extract results for {gp} {year}: {e}")
        return None

def fetch_all_laps(races, session_type="R"):
    all_laps = []
    all_results = []   # ← ADD THIS

    for year, gp in races:
        print(f"Fetching laps: {year} {gp}...")
        session = fastf1.get_session(year, gp, session_type)
        session.load()

        # Laps — existing logic unchanged
        laps = session.laps.copy()
        laps["Race"] = gp
        laps["Year"] = year
        all_laps.append(laps)
        print(f"  {gp} {year}: {len(laps)} laps")

        # ↓ ADD THIS BLOCK — extract results from the same session object
        race_results = fetch_race_results(session, gp, year)
        if race_results is not None:
            all_results.append(race_results)
            print(f"  {gp} {year}: {len(race_results)} classified finishers")

    # ↓ ADD THIS BLOCK — save results to DuckDB
    if all_results:
        combined_results = pd.concat(all_results, ignore_index=True)
        con = duckdb.connect(DB_PATH)
        con.register("results_df", combined_results)
        con.execute("""
            CREATE OR REPLACE TABLE race_results AS
            SELECT * FROM results_df
        """)
        con.close()
        print(f"\nSaved race_results table to DuckDB ({len(combined_results)} rows)")

    return pd.concat(all_laps, ignore_index=True)

if __name__ == "__main__":
    combined = fetch_all_laps(RACES_2023)
    print(f"\nTotal: {len(combined)} laps across {combined['Race'].nunique()} races")
    combined.to_csv("/app/data/processed/laps_2023.csv", index=False)
    print("Saved to CSV")