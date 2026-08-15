import duckdb
import matplotlib.pyplot as plt

DB_PATH = "/app/data/processed/telemetry.duckdb"

def lap_comparison(driver_a="VER", driver_b="LEC"):
    con = duckdb.connect(DB_PATH)
    delta = con.execute("SELECT * FROM delta_ver_lec ORDER BY Distance").df()
    con.close()

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    axes[0].plot(delta["Distance"], delta[f"Speed_{driver_a}"], label=driver_a)
    axes[0].plot(delta["Distance"], delta[f"Speed_{driver_b}"], label=driver_b)
    axes[0].set_ylabel("Speed (km/h)")
    axes[0].legend()
    axes[0].set_title(f"Speed Trace: {driver_a} vs {driver_b}")

    axes[1].plot(delta["Distance"], delta["Delta"], color="red")
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].set_ylabel(f"Delta (s) [{driver_b} - {driver_a}]")
    axes[1].set_xlabel("Distance (m)")
    axes[1].set_title("Time Delta")

    plt.tight_layout()
    plt.savefig("/app/data/processed/lap_comparison_ver_lec.png", dpi=120)
    print("Saved plot to data/processed/lap_comparison_ver_lec.png")

    final_delta = delta["Delta"].iloc[-1]

    # rate of change of cumulative delta = local gain/loss per step
    delta["Delta_rate"] = delta["Delta"].diff()
    max_gain_idx = delta["Delta_rate"].idxmin()  # driver_a gaining fastest here
    max_loss_idx = delta["Delta_rate"].idxmax()  # driver_b gaining fastest here

    print(f"\nFinal delta: {final_delta:.3f}s ({driver_b} {'behind' if final_delta > 0 else 'ahead'})")
    print(f"Fastest {driver_a} gain zone: near distance {delta['Distance'].iloc[max_gain_idx]:.0f}m")
    print(f"Fastest {driver_b} gain zone: near distance {delta['Distance'].iloc[max_loss_idx]:.0f}m")

if __name__ == "__main__":
    lap_comparison()