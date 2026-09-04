import duckdb

DB_PATH = "/app/data/processed/telemetry.duckdb"
CSV_PATH = "/app/data/processed/all_drivers_bahrain_2024_telemetry.csv"

def load_telemetry_all():
    con = duckdb.connect(DB_PATH)
    con.execute(f"""
        CREATE OR REPLACE TABLE telemetry_all AS
        SELECT * FROM read_csv_auto('{CSV_PATH}')
    """)
    result = con.execute("SELECT COUNT(*) FROM telemetry_all").fetchone()
    drivers = con.execute("SELECT COUNT(DISTINCT Driver) FROM telemetry_all").fetchone()
    print(f"Loaded {result[0]} rows, {drivers[0]} drivers into telemetry_all table")
    con.close()

if __name__ == "__main__":
    load_telemetry_all()