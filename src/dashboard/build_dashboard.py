import duckdb
import plotly.graph_objects as go
import plotly.io as pio

DB_PATH = "/app/data/processed/telemetry.duckdb"
OUTPUT_PATH = "/app/data/processed/dashboard.html"

def load_data():
    con = duckdb.connect(DB_PATH)
    delta = con.execute("SELECT * FROM delta_vs_fastest WHERE Driver = 'LEC' ORDER BY Distance").df()
    corner_avg = con.execute("SELECT * FROM corner_ranking_avg ORDER BY rank").df()
    driver_comp = con.execute("SELECT * FROM driver_comparison_all ORDER BY rank").df()
    deg_multi = con.execute("SELECT * FROM tire_degradation_multi_race").df()
    mc_multi = con.execute("SELECT * FROM monte_carlo_multi_race").df()
    pit_multi = con.execute("SELECT * FROM pit_optimizer_multi_race ORDER BY Race").df()
    con.close()
    return delta, corner_avg, driver_comp, deg_multi, mc_multi, pit_multi

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
        y=corner_avg["avg_time_lost"], marker_color="#dc0000"
    ))
    fig.update_layout(title="Corner Ranking: Avg Time Lost vs Fastest Driver (Full Grid, Bahrain 2024)",
                       xaxis_title="Corner", yaxis_title="Avg Time Lost (s)", height=400)
    return fig

def build_driver_comparison_fig(driver_comp):
    fig = go.Figure(go.Bar(x=driver_comp["Driver"], y=driver_comp["best_lap"], marker_color="#1e90ff"))
    fig.update_layout(title="Best Lap Time, Full Grid (Bahrain 2024)",
                       xaxis_title="Driver", yaxis_title="Best Lap (s)", height=400)
    fig.update_yaxes(range=[driver_comp["best_lap"].min() - 1, driver_comp["best_lap"].max() + 1])
    return fig

def build_deg_multi_race_fig_with_filter(deg_multi):
    races = sorted(deg_multi["Race"].unique())
    compound_colors = {"SOFT": "#dc0000", "MEDIUM": "#ffd700", "HARD": "#f0f0f0"}

    fig = go.Figure()
    trace_race_map = []
    for race in races:
        race_data = deg_multi[deg_multi["Race"] == race].groupby("Compound")["deg_rate_sec_per_lap"].mean().reset_index()
        for _, row in race_data.iterrows():
            fig.add_trace(go.Bar(
                x=[row["Compound"]], y=[row["deg_rate_sec_per_lap"]],
                name=row["Compound"], marker_color=compound_colors.get(row["Compound"], "#999"),
                marker_line=dict(width=1, color="black"),
                visible=(race == races[0])
            ))
            trace_race_map.append(race)

    buttons = []
    for race in races:
        visibility = [r == race for r in trace_race_map]
        buttons.append(dict(label=race, method="update", args=[{"visible": visibility}, {"title": f"Tire Degradation Rate by Compound — {race} 2024"}]))

    fig.update_layout(
        title=f"Tire Degradation Rate by Compound — {races[0]} 2024",
        xaxis_title="Compound", yaxis_title="Deg Rate (sec/lap)", height=400, showlegend=False,
        updatemenus=[dict(active=0, buttons=buttons, x=1.0, y=1.2, xanchor="right")]
    )
    return fig

def build_pit_summary_fig(pit_multi):
    fig = go.Figure(go.Bar(
        x=pit_multi["Race"], y=pit_multi["mean_total_time"],
        text=[f"{c1}→{c2}, lap {int(pl)}" for c1, c2, pl in zip(pit_multi["compound_1"], pit_multi["compound_2"], pit_multi["pit_lap"])],
        textposition="outside", marker_color="#00d2be"
    ))
    fig.update_layout(title="Optimal Pit Strategy & Predicted Race Time, All 8 Races (2024)",
                       xaxis_title="Race", yaxis_title="Predicted Race Time (s)", height=450)
    return fig

if __name__ == "__main__":
    delta, corner_avg, driver_comp, deg_multi, mc_multi, pit_multi = load_data()

    figs = [
        build_delta_fig(delta),
        build_corner_ranking_fig(corner_avg),
        build_driver_comparison_fig(driver_comp),
        build_deg_multi_race_fig_with_filter(deg_multi),
        build_pit_summary_fig(pit_multi),
    ]

    with open(OUTPUT_PATH, "w") as f:
        f.write("<html><head><title>F1 Telemetry & Strategy Dashboard</title>")
        f.write("<style>body{font-family:Arial;background:#f5f5f5;margin:20px;} h1{color:#1a1a2e;}</style>")
        f.write("</head><body>")
        f.write("<h1>F1 Telemetry & Strategy Dashboard</h1>")
        f.write("<p>Full grid (20 drivers) across 8 races, 2024 season. Telemetry/corner analysis shown for Bahrain; tire degradation and pit strategy scaled to all 8 races.</p>")
        f.write("<p style='color:#666;font-size:0.9em;'>Note: some races show near-zero or negative degradation rates, a known model limitation on low-degradation circuits with limited sample size, not a data error. See README for details.</p>")
        for fig in figs:
            f.write(pio.to_html(fig, full_html=False, include_plotlyjs="cdn"))
        f.write("</body></html>")

    print(f"Dashboard saved to {OUTPUT_PATH}")