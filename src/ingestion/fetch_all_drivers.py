import fastf1
import os
import pandas as pd

CACHE_DIR = os.environ.get("FASTF1_CACHE", "/app/data/raw/fastf1_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

DRIVERS = ["VER", "PER", "LEC", "SAI", "HAM", "RUS", "NOR", "PIA",
           "ALO", "STR", "GAS", "OCO", "TSU", "RIC", "ALB", "SAR",
           "BOT", "ZHO", "MAG", "HUL"]

def fetch_all_telemetry(year, gp, session_type="R", drivers=DRIVERS):
    session = fastf1.get_session(year, gp, session_type)
    session.load()

    all_telemetry = []
    for driver in drivers:
        try:
            driver_laps = session.laps.pick_driver(driver)
            if len(driver_laps) == 0:
                print(f"Skipping {driver}: no laps found")
                continue
            lap = driver_laps.pick_fastest()
            telemetry = lap.get_telemetry()
            telemetry["Driver"] = driver
            telemetry["LapNumber"] = lap["LapNumber"]
            all_telemetry.append(telemetry)
            print(f"Fetched {driver}: {len(telemetry)} points, lap {lap['LapNumber']}")
        except Exception as e:
            print(f"Failed {driver}: {e}")

    combined = pd.concat(all_telemetry, ignore_index=True)
    return combined

if __name__ == "__main__":
    combined = fetch_all_telemetry(2024, "Bahrain", "R")
    print(f"\nTotal rows: {len(combined)}, drivers: {combined['Driver'].nunique()}")
    combined.to_csv("/app/data/processed/all_drivers_bahrain_2024_telemetry.csv", index=False)
    print("Saved to CSV")
