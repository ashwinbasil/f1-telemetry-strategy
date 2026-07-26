import fastf1
import os

CACHE_DIR = os.environ.get("FASTF1_CACHE", "/app/data/raw/fastf1_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

def fetch_session(year: int, gp: str, session_type: str = "R"):
    """
    year: e.g. 2024
    gp: race name, e.g. 'Bahrain'
    session_type: 'R' race, 'Q' quali, 'FP1'/'FP2'/'FP3' practice
    """
    session = fastf1.get_session(year, gp, session_type)
    session.load()
    return session

if __name__ == "__main__":
    session = fetch_session(2024, "Bahrain", "R")
    print(f"Loaded: {session}")
    print(f"Laps available: {len(session.laps)}")
    laps = session.laps
    laps.to_csv("/app/data/processed/bahrain_2024_race_laps.csv", index=False)
    print("Saved laps to CSV")
