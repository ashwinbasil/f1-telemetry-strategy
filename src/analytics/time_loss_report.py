import duckdb

DB_PATH = "/app/data/processed/telemetry.duckdb"

def time_loss_report():
    con = duckdb.connect(DB_PATH)
    corner_avg = con.execute("SELECT * FROM corner_ranking_avg ORDER BY rank").df()
    driver_comp = con.execute("SELECT * FROM driver_comparison_all ORDER BY rank").df()
    con.close()

    fastest = driver_comp.iloc[0]
    slowest = driver_comp.iloc[-1]
    gap = slowest["best_lap"] - fastest["best_lap"]

    print("=" * 55)
    print("TIME LOSS REPORT — Bahrain 2024, Full Grid")
    print("=" * 55)

    print(f"\nFastest: {fastest['Driver']} ({fastest['best_lap']:.3f}s)")
    print(f"Slowest: {slowest['Driver']} ({slowest['best_lap']:.3f}s)")
    print(f"Field spread: {gap:.3f}s")

    print(f"\nTop 5 drivers by best lap:")
    print(driver_comp.head(5)[["rank", "Driver", "best_lap", "avg_lap", "std_lap"]].to_string(index=False))

    print(f"\nTop 3 corners by avg time lost across field (vs fastest driver):")
    top3 = corner_avg.head(3)
    for _, row in top3.iterrows():
        print(f"  Corner {int(row['corner_number'])}: {row['avg_time_lost']:.3f}s avg loss")

    print("=" * 55)

if __name__ == "__main__":
    time_loss_report()