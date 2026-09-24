import duckdb

DB_PATH = "/app/data/processed/telemetry.duckdb"

def load_2023():
    con = duckdb.connect(DB_PATH)

    con.execute("""
        CREATE OR REPLACE TABLE telemetry_2023 AS
        SELECT * FROM read_csv_auto('/app/data/processed/telemetry_2023.csv')
    """)
    con.execute("""
        CREATE OR REPLACE TABLE laps_2023 AS
        SELECT * FROM read_csv_auto('/app/data/processed/laps_2023.csv')
    """)

    t = con.execute("SELECT COUNT(*) FROM telemetry_2023").fetchone()
    l = con.execute("SELECT COUNT(*) FROM laps_2023").fetchone()
    print(f"telemetry_2023: {t[0]} rows")
    print(f"laps_2023: {l[0]} rows")

    con.close()

def merge_multi_year():
    con = duckdb.connect(DB_PATH)

    con.execute("""
        CREATE OR REPLACE TABLE telemetry_multi_year AS
        SELECT * FROM telemetry_multi_race
        UNION ALL BY NAME
        SELECT * FROM telemetry_2023
    """)
    con.execute("""
        CREATE OR REPLACE TABLE laps_multi_year AS
        SELECT * FROM laps_multi_race
        UNION ALL BY NAME
        SELECT * FROM laps_2023
    """)

    t = con.execute("SELECT COUNT(*), COUNT(DISTINCT Year) FROM telemetry_multi_year").fetchone()
    l = con.execute("SELECT COUNT(*), COUNT(DISTINCT Year) FROM laps_multi_year").fetchone()
    print(f"telemetry_multi_year: {t[0]} rows, {t[1]} years")
    print(f"laps_multi_year: {l[0]} rows, {l[1]} years")

    con.close()

if __name__ == "__main__":
    load_2023()
    merge_multi_year()