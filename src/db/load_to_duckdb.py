import duckdb

DB_PATH = "/app/data/processed/telemetry.duckdb"
CSV_PATH = "/app/data/processed/bahrain_2024_race_laps.csv"

def load_data():
    con = duckdb.connect(DB_PATH)
    
    con.execute(f"""
        CREATE OR REPLACE TABLE laps AS
        SELECT * FROM read_csv_auto('{CSV_PATH}')
    """)
    
    result = con.execute("SELECT COUNT(*) FROM laps").fetchone()
    print(f"Loaded {result[0]} rows into DuckDB")
    
    cols = con.execute("DESCRIBE laps").fetchall()
    print(f"Columns ({len(cols)}):")
    for c in cols:
        print(f"  {c[0]}: {c[1]}")
    
    con.close()

if __name__ == "__main__":
    load_data()
