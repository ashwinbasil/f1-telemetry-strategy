import duckdb
import numpy as np
import pandas as pd

DB_PATH = "/app/data/processed/telemetry.duckdb"

def compute_delta(driver_a_table="telemetry", driver_b_table="telemetry_lec", driver_a_name="VER", driver_b_name="LEC"):
    con = duckdb.connect(DB_PATH)
    df_a = con.execute(f"SELECT Distance, Time, Speed FROM {driver_a_table} ORDER BY Distance").df()
    df_b = con.execute(f"SELECT Distance, Time, Speed FROM {driver_b_table} ORDER BY Distance").df()
    con.close()

    df_a = df_a.dropna(subset=["Distance"]).drop_duplicates(subset=["Distance"])
    df_b = df_b.dropna(subset=["Distance"]).drop_duplicates(subset=["Distance"])

    def time_to_seconds(t):
        return pd.to_timedelta(t).total_seconds()

    df_a["Time_sec"] = df_a["Time"].apply(time_to_seconds)
    df_b["Time_sec"] = df_b["Time"].apply(time_to_seconds)

    common_distance = np.linspace(
        max(df_a["Distance"].min(), df_b["Distance"].min()),
        min(df_a["Distance"].max(), df_b["Distance"].max()),
        1000
    )

    time_a_interp = np.interp(common_distance, df_a["Distance"], df_a["Time_sec"])
    time_b_interp = np.interp(common_distance, df_b["Distance"], df_b["Time_sec"])
    speed_a_interp = np.interp(common_distance, df_a["Distance"], df_a["Speed"])
    speed_b_interp = np.interp(common_distance, df_b["Distance"], df_b["Speed"])

    delta = time_b_interp - time_a_interp  # positive = driver_b slower (behind)

    result = pd.DataFrame({
        "Distance": common_distance,
        f"Time_{driver_a_name}": time_a_interp,
        f"Time_{driver_b_name}": time_b_interp,
        f"Speed_{driver_a_name}": speed_a_interp,
        f"Speed_{driver_b_name}": speed_b_interp,
        "Delta": delta
    })

    return result

if __name__ == "__main__":
    result = compute_delta()
    print(f"Delta computed over {len(result)} points")
    print(f"Final delta (end of lap): {result['Delta'].iloc[-1]:.3f}s")
    print(result.head(10).to_string())
    print("...")
    print(result.tail(5).to_string())

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE delta_ver_lec AS SELECT * FROM result")
    con.close()
    print("Saved delta_ver_lec table to DuckDB")