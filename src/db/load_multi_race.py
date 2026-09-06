import duckdb

DB_PATH = "/app/data/processed/telemetry.duckdb"

def load_telemetry():
    con = duckdb.connect(DB_PATH)
    con.execute("""
        CREATE OR REPLACE TABLE telemetry_multi_race AS
        SELECT * FROM read_csv_auto('/app/data/processed/multi_race_telemetry.csv')
    """)
    result = con.execute("SELECT COUNT(*) FROM telemetry_multi_race").fetchone()
    races = con.execute("SELECT COUNT(DISTINCT Race) FROM telemetry_multi_race").fetchone()
    print(f"telemetry_multi_race: {result[0]} rows, {races[0]} races")
    con.close()

def load_laps():
    con = duckdb.connect(DB_PATH)
    con.execute("""
        CREATE OR REPLACE TABLE laps_multi_race AS
        SELECT * FROM read_csv_auto('/app/data/processed/multi_race_laps.csv')
    """)
    result = con.execute("SELECT COUNT(*) FROM laps_multi_race").fetchone()
    races = con.execute("SELECT COUNT(DISTINCT Race) FROM laps_multi_race").fetchone()
    print(f"laps_multi_race: {result[0]} rows, {races[0]} races")
    con.close()

if __name__ == "__main__":
    load_telemetry()
    load_laps()