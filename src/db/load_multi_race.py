import duckdb

DB_PATH = "/app/data/processed/telemetry.duckdb"
CSV_PATH = "/app/data/processed/multi_race_telemetry.csv"

def load_multi_race():
    con = duckdb.connect(DB_PATH)
    con.execute(f"""
        CREATE OR REPLACE TABLE telemetry_multi_race AS
        SELECT * FROM read_csv_auto('{CSV_PATH}')
    """)
    result = con.execute("SELECT COUNT(*) FROM telemetry_multi_race").fetchone()
    races = con.execute("SELECT COUNT(DISTINCT Race) FROM telemetry_multi_race").fetchone()
    print(f"Loaded {result[0]} rows across {races[0]} races into telemetry_multi_race table")
    con.close()

if __name__ == "__main__":
    load_multi_race()