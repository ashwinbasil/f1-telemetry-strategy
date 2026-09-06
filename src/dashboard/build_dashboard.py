import duckdb
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

DB_PATH = "/app/data/processed/telemetry.duckdb"
OUTPUT_PATH = "/app/data/processed/dashboard.html"

def load_data():
    con = duckdb.connect(DB_PATH)
    delta = con.execute("SELECT * FROM delta_vs_fastest WHERE Driver = 'LEC' ORDER BY Distance").df()
    corner_avg = con.execute("SELECT * FROM corner_ranking_avg ORDER BY rank").df()
    driver_comp = con.execute("SELECT * FROM driver_comparison_all ORDER BY rank").df()
    deg_multi = con.execute("SELECT * FROM tire_degradation_multi_race").df()
    mc_results = con.execute("SELECT * FROM monte_carlo_results ORDER BY mean_total_time").df()
    pit_rec = con.execute("SELECT * FROM pit_optimizer_recommendations ORDER BY mean_total_time").df()
    con.close()
    return delta, corner_avg, driver_comp, deg_multi, mc_results, pit_rec

def build_delta_fig(delta):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=delta["Distance"], y=delta["Delta"], line=dict(color="orange")))
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(title="LEC Time Delta vs Session Fastest (VER) — Bahrain 2024",
                       xaxis_title="Distance (m)", yaxis_title="Delta (s)", height=350)
    return fig

def build_corner_ranking_fig(corner_avg):
    fig = go.Figure(go.Bar(
        x=[f"Corner {int(c)}" for c in corner_avg["corner_number"]],
        y=corner_avg["avg_time_lost"],
        marker_color="#dc0000"
    ))
    fig.update_layout(title="Corner Ranking: Avg Time Lost vs Fastest Driver (Full Grid, Bahrain 2024)",
                       xaxis_title="Corner", yaxis_title="Avg Time Lost (s)", height=400)
    return fig

def build_driver_comparison_fig(driver_comp):
    fig = go.Figure(go.Bar(
        x=driver_comp["Driver"],
        y=driver_comp["best_lap"],
        marker_color="#1e90ff"
    ))
    fig.update_layout(title="Best Lap Time, Full Grid (Bahrain 2024)",
                       xaxis_title="Driver", yaxis_title="Best Lap (s)", height=400)
    fig.update_yaxes(range=[driver_comp["best_lap"].min() - 1, driver_comp["best_lap"].max() + 1])
    return fig

def build_deg_multi_race_fig(deg_multi):
    summary = deg_multi.groupby(["Race", "Compound"])["deg_rate_sec_per_lap"].mean().reset_index()
    fig = go.Figure()
    for compound, color in [("SOFT", "#dc0000"), ("MEDIUM", "#ffd700"), ("HARD", "#f0f0f0")]:
        subset = summary[summary["Compound"] == compound]
        if len(subset) > 0:
            fig.add_trace(go.Bar(x=subset["Race"], y=subset["deg_rate_sec_per_lap"], name=compound, marker_color=color, marker_line=dict(width=1, color="black")))
    fig.update_layout(title="Tire Degradation Rate by Compound, Across 3 Races",
                       xaxis_title="Race", yaxis_title="Deg Rate (sec/lap)", barmode="group", height=400)
    return fig

def build_strategy_fig(mc_results):
    mc_results["label"] = mc_results["compound_1"] + "→" + mc_results["compound_2"] + " (lap " + mc_results["pit_lap"].astype(str) + ")"
    top10 = mc_results.nsmallest(10, "mean_total_time")
    fig = go.Figure(go.Bar(
        x=top10["mean_total_time"], y=top10["label"], orientation="h", marker_color="#00d2be",
        error_x=dict(type="data", array=(top10["p90"] - top10["mean_total_time"]))
    ))
    fig.update_layout(title="Top 10 Pit Strategies (Monte Carlo, Bahrain 2024)",
                       xaxis_title="Predicted Race Time (s)", height=500)
    fig.update_xaxes(range=[top10["mean_total_time"].min() - 5, top10["mean_total_time"].max() + 5])
    fig.update_yaxes(autorange="reversed")
    return fig

def build_pit_recommendation_table(pit_rec):
    fig = go.Figure(data=[go.Table(
        header=dict(values=["Strategy", "Pit Lap", "Predicted Time (s)", "Gap to Best (s)"],
                    fill_color="#1a1a2e", font=dict(color="white"), align="left"),
        cells=dict(values=[
            pit_rec["compound_1"] + " → " + pit_rec["compound_2"],
            pit_rec["pit_lap"],
            pit_rec["mean_total_time"].round(2),
            (pit_rec["mean_total_time"] - pit_rec["mean_total_time"].min()).round(2)
        ], align="left")
    )])
    fig.update_layout(title="Pit Stop Optimizer Recommendations (Bahrain 2024)", height=300)
    return fig

if __name__ == "__main__":
    delta, corner_avg, driver_comp, deg_multi, mc_results, pit_rec = load_data()

    figs = [
        build_delta_fig(delta),
        build_corner_ranking_fig(corner_avg),
        build_driver_comparison_fig(driver_comp),
        build_deg_multi_race_fig(deg_multi),
        build_strategy_fig(mc_results),
        build_pit_recommendation_table(pit_rec)
    ]

    with open(OUTPUT_PATH, "w") as f:
        f.write("<html><head><title>F1 Telemetry & Strategy Dashboard</title>")
        f.write("<style>body{font-family:Arial;background:#f5f5f5;margin:20px;} h1{color:#1a1a2e;}</style>")
        f.write("</head><body>")
        f.write("<h1>F1 Telemetry & Strategy Dashboard</h1>")
        f.write("<p>Full grid (20 drivers), Bahrain 2024 + multi-race tire degradation (Bahrain, Saudi Arabia, Australia 2024)</p>")
        f.write("<p style='color:#666;font-size:0.9em;'>Note: Australia/Saudi Arabia show near-zero or negative degradation rates, a known model limitation on low-degradation circuits with limited sample size, not a data error. See README for details.</p>")
        for fig in figs:
            f.write(pio.to_html(fig, full_html=False, include_plotlyjs="cdn"))
        f.write("</body></html>")

    print(f"Dashboard saved to {OUTPUT_PATH}")