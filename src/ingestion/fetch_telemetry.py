import fastf1
import os

CACHE_DIR = os.environ.get("FASTF1_CACHE", "/app/data/raw/fastf1_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

def fetch_lap_telemetry(year: int, gp: str, session_type: str, driver: str, lap_number: int = None):
    session = fastf1.get_session(year, gp, session_type)
    session.load()
    
    driver_laps = session.laps.pick_driver(driver)
    
    if lap_number:
        lap = driver_laps[driver_laps['LapNumber'] == lap_number].iloc[0]
    else:
        lap = driver_laps.pick_fastest()
    
    telemetry = lap.get_telemetry()
    return telemetry, lap

if __name__ == "__main__":
    telemetry, lap = fetch_lap_telemetry(2024, "Bahrain", "R", "VER")
    print(f"Lap: {lap['LapNumber']}, Time: {lap['LapTime']}")
    print(f"Telemetry points: {len(telemetry)}")
    print(telemetry.columns.tolist())
    telemetry.to_csv("/app/data/processed/ver_bahrain_2024_fastest_lap_telemetry.csv", index=False)
    print("Saved telemetry to CSV")
