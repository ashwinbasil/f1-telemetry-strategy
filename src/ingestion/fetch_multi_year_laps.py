
import fastf1
import os
import pandas as pd

CACHE_DIR = os.environ.get("FASTF1_CACHE", "/app/data/raw/fastf1_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

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

def fetch_all_laps(races, session_type="R"):
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
    return pd.concat(all_laps, ignore_index=True)

if __name__ == "__main__":
    combined = fetch_all_laps(RACES_2023)
    print(f"\nTotal: {len(combined)} laps across {combined['Race'].nunique()} races")
    combined.to_csv("/app/data/processed/laps_2023.csv", index=False)
    print("Saved to CSV")