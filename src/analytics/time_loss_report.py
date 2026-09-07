import duckdb

DB_PATH = "/app/data/processed/telemetry.duckdb"

def time_loss_report():
    con = duckdb.connect(DB_PATH)
    corner_avg = con.execute("SELECT * FROM corner_ranking_avg_multi_race").df()
    driver_comp = con.execute("SELECT * FROM driver_comparison_multi_race").df()
    con.close()

    print("=" * 60)
    print("TIME LOSS REPORT — Full Grid, 8 Races, 2024")
    print("=" * 60)

    for race in sorted(driver_comp["Race"].unique()):
        race_drivers = driver_comp[driver_comp["Race"] == race].sort_values("rank")
        race_corners = corner_avg[corner_avg["Race"] == race].sort_values("avg_time_lost", ascending=False)

        fastest = race_drivers.iloc[0]
        slowest = race_drivers.iloc[-1]
        gap = slowest["best_lap"] - fastest["best_lap"]
        worst_corner = race_corners.iloc[0]

        print(f"\n{race}:")
        print(f"  Fastest: {fastest['Driver']} ({fastest['best_lap']:.3f}s) — Slowest: {slowest['Driver']} ({slowest['best_lap']:.3f}s) — Spread: {gap:.3f}s")
        print(f"  Worst corner: {int(worst_corner['corner_number'])} ({worst_corner['avg_time_lost']:.3f}s avg loss)")

    print("=" * 60)

if __name__ == "__main__":
    time_loss_report()