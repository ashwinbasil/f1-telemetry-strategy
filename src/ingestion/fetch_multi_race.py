import fastf1
import os
import pandas as pd

CACHE_DIR = os.environ.get("FASTF1_CACHE", "/app/data/raw/fastf1_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

DRIVERS = ["VER", "PER", "LEC", "SAI", "HAM", "RUS", "NOR", "PIA",
           "ALO", "STR", "GAS", "OCO", "TSU", "RIC", "ALB", "SAR",
           "BOT", "ZHO", "MAG", "HUL"]

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

def fetch_race_telemetry(year, gp, session_type="R", drivers=DRIVERS):
    session = fastf1.get_session(year, gp, session_type)
    session.load()

    all_telemetry = []
    for driver in drivers:
        try:
            driver_laps = session.laps.pick_driver(driver)
            if len(driver_laps) == 0:
                print(f"  Skipping {driver}: no laps found")
                continue
            lap = driver_laps.pick_fastest()
            telemetry = lap.get_telemetry()
            telemetry["Driver"] = driver
            telemetry["LapNumber"] = lap["LapNumber"]
            telemetry["Race"] = gp
            telemetry["Year"] = year
            all_telemetry.append(telemetry)
        except Exception as e:
            print(f"  Failed {driver}: {e}")

    if len(all_telemetry) == 0:
        return None

    combined = pd.concat(all_telemetry, ignore_index=True)
    return combined

def fetch_all_races(races=RACES, drivers=DRIVERS):
    all_races_telemetry = []
    for year, gp in races:
        print(f"Fetching {year} {gp}...")
        race_df = fetch_race_telemetry(year, gp, drivers=drivers)
        if race_df is not None:
            all_races_telemetry.append(race_df)
            print(f"  {gp} {year}: {len(race_df)} rows, {race_df['Driver'].nunique()} drivers")

    combined = pd.concat(all_races_telemetry, ignore_index=True)
    return combined

if __name__ == "__main__":
    combined = fetch_all_races()
    print(f"\nTotal: {len(combined)} rows across {combined['Race'].nunique()} races, {combined['Driver'].nunique()} drivers")
    combined.to_csv("/app/data/processed/multi_race_telemetry.csv", index=False)
    print("Saved to CSV")