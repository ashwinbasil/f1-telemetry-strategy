import fastf1
import os
import pandas as pd

CACHE_DIR = os.environ.get("FASTF1_CACHE", "/app/data/raw/fastf1_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

RACES = [
    (2024, "Bahrain"),
    (2024, "Saudi Arabia"),
    (2024, "Australia"),
    (2024, "Monaco"),
    (2024, "Singapore"),
    (2024, "Belgium"),
    (2024, "Japan"),
    (2024, "Monza"),
]

def fetch_all_laps(races=RACES, session_type="R"):
    all_laps = []
    for year, gp in races:
        print(f"Fetching laps: {year} {gp}...")
        session = fastf1.get_session(year, gp, session_type)
        session.load()
        laps = session.laps.copy()
        laps["Race"] = gp
        laps["Year"] = year
        all_laps.append(laps)
        print(f"  {gp} {year}: {len(laps)} laps")

    combined = pd.concat(all_laps, ignore_index=True)
    return combined

if __name__ == "__main__":
    combined = fetch_all_laps()
    print(f"\nTotal: {len(combined)} laps across {combined['Race'].nunique()} races")
    combined.to_csv("/app/data/processed/multi_race_laps.csv", index=False)
    print("Saved to CSV")