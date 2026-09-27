import fastf1
import os
import pandas as pd

CACHE_DIR = os.environ.get("FASTF1_CACHE", "/app/data/raw/fastf1_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

RACES = [
    (2023, "Bahrain"), (2023, "Saudi Arabia"), (2023, "Australia"), (2023, "Monaco"),
    (2023, "Singapore"), (2023, "Belgium"), (2023, "Japan"), (2023, "Monza"),
    (2024, "Bahrain"), (2024, "Saudi Arabia"), (2024, "Australia"), (2024, "Monaco"),
    (2024, "Singapore"), (2024, "Belgium"), (2024, "Japan"), (2024, "Monza"),
]

def fetch_all_weather(races=RACES, session_type="R"):
    all_weather = []
    for year, gp in races:
        print(f"Fetching weather: {year} {gp}...")
        session = fastf1.get_session(year, gp, session_type)
        session.load()
        weather = session.weather_data.copy()
        weather["Race"] = gp
        weather["Year"] = year
        all_weather.append(weather)
        print(f"  {gp} {year}: {len(weather)} weather samples, TrackTemp range {weather['TrackTemp'].min():.1f}-{weather['TrackTemp'].max():.1f}C")
    return pd.concat(all_weather, ignore_index=True)

if __name__ == "__main__":
    combined = fetch_all_weather()
    print(f"\nTotal: {len(combined)} weather samples across {combined['Race'].nunique()} races, {combined['Year'].nunique()} years")
    combined.to_csv("/app/data/processed/weather_multi_year.csv", index=False)
    print("Saved to CSV")