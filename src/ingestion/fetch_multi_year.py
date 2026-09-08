import fastf1



import os



import pandas as pd









CACHE_DIR = os.environ.get("FASTF1_CACHE", "/app/data/raw/fastf1_cache")



os.makedirs(CACHE_DIR, exist_ok=True)



fastf1.Cache.enable_cache(CACHE_DIR)









DRIVERS = ["VER", "PER", "LEC", "SAI", "HAM", "RUS", "NOR", "PIA",



           "ALO", "STR", "GAS", "OCO", "TSU", "RIC", "ALB", "SAR",



           "BOT", "ZHO", "MAG", "HUL"]









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



    return pd.concat(all_telemetry, ignore_index=True)









def fetch_all_races(races, drivers=DRIVERS):



    all_races_telemetry = []



    for year, gp in races:



        print(f"Fetching {year} {gp}...")



        race_df = fetch_race_telemetry(year, gp, drivers=drivers)



        if race_df is not None:



            all_races_telemetry.append(race_df)



            print(f"  {gp} {year}: {len(race_df)} rows, {race_df['Driver'].nunique()} drivers")



    return pd.concat(all_races_telemetry, ignore_index=True)









if __name__ == "__main__":



    combined = fetch_all_races(RACES_2023)



    print(f"\nTotal: {len(combined)} rows across {combined['Race'].nunique()} races, {combined['Driver'].nunique()} drivers")



    combined.to_csv("/app/data/processed/telemetry_2023.csv", index=False)



    print("Saved to CSV")