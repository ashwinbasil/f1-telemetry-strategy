import duckdb

DB_PATH = "/app/data/processed/telemetry.duckdb"
CSV_PATH = "/app/data/processed/lec_bahrain_2024_fastest_lap_telemetry.csv"

def load_telemetry():
    con = duckdb.connect(DB_PATH)
    con.execute(f"""
        CREATE OR REPLACE TABLE telemetry_lec AS
        SELECT * FROM read_csv_auto('{CSV_PATH}')
    """)
    result = con.execute("SELECT COUNT(*) FROM telemetry_lec").fetchone()
    print(f"Loaded {result[0]} rows into telemetry_lec table")
    con.close()

if __name__ == "__main__":
    load_telemetry()
