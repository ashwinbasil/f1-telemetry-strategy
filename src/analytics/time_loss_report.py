import duckdb

DB_PATH = "/app/data/processed/telemetry.duckdb"

def time_loss_report(driver_a="VER", driver_b="LEC"):
    con = duckdb.connect(DB_PATH)
    corner_rank = con.execute("SELECT * FROM corner_ranking ORDER BY rank").df()
    driver_comp = con.execute("SELECT * FROM driver_comparison").df()
    delta = con.execute("SELECT * FROM delta_ver_lec ORDER BY Distance").df()
    con.close()

    final_delta = delta["Delta"].iloc[-1]

    print("=" * 50)
    print(f"TIME LOSS REPORT: {driver_a} vs {driver_b}")
    print("=" * 50)

    print(f"\nFastest lap gap: {abs(final_delta):.3f}s ({driver_b if final_delta > 0 else driver_a} slower)")

    print(f"\nRace pace (56 laps):")
    print(driver_comp.set_index("Driver")[["avg_lap", "best_lap", "std_lap"]].to_string())

    print(f"\nTop 3 corners by time impact:")
    top3 = corner_rank.head(3)
    for _, row in top3.iterrows():
        print(f"  Corner {int(row['corner_number'])}: {row['delta_swing']:+.3f}s ({row['winner']} faster)")

    total_ver_corners = corner_rank[corner_rank["winner"] == driver_a]["abs_swing"].sum()
    total_lec_corners = corner_rank[corner_rank["winner"] == driver_b]["abs_swing"].sum()
    print(f"\nTotal corner-zone time won: {driver_a}={total_ver_corners:.3f}s, {driver_b}={total_lec_corners:.3f}s")
    print("=" * 50)

if __name__ == "__main__":
    time_loss_report()