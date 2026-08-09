import fastf1
import os

CACHE_DIR = os.environ.get("FASTF1_CACHE", "/app/data/raw/fastf1_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

def fetch_lap_telemetry(year, gp, session_type, driver, lap_number=None):
    session = fastf1.get_session(year, gp, session_type)
    session.load()
    driver_laps = session.laps.pick_driver(driver)
    lap = driver_laps[driver_laps['LapNumber'] == lap_number].iloc[0] if lap_number else driver_laps.pick_fastest()
    telemetry = lap.get_telemetry()
    return telemetry, lap

if __name__ == "__main__":
    telemetry, lap = fetch_lap_telemetry(2024, "Bahrain", "R", "LEC")
    print(f"Lap: {lap['LapNumber']}, Time: {lap['LapTime']}")
    print(f"Telemetry points: {len(telemetry)}")
    telemetry.to_csv("/app/data/processed/lec_bahrain_2024_fastest_lap_telemetry.csv", index=False)
    print("Saved telemetry to CSV")
