import duckdb
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

DB_PATH = "/app/data/processed/telemetry.duckdb"
OUTPUT_PATH = "/app/data/processed/dashboard.html"

def load_data():
    con = duckdb.connect(DB_PATH)
    delta = con.execute("SELECT * FROM delta_ver_lec ORDER BY Distance").df()
    corner_rank = con.execute("SELECT * FROM corner_ranking ORDER BY rank").df()
    mc_results = con.execute("SELECT * FROM monte_carlo_results ORDER BY mean_total_time").df()
    pit_rec = con.execute("SELECT * FROM pit_optimizer_recommendations ORDER BY mean_total_time").df()
    con.close()
    return delta, corner_rank, mc_results, pit_rec

def build_lap_comparison_fig(delta):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                         subplot_titles=("Speed Trace: VER vs LEC", "Time Delta (VER vs LEC)"),
                         vertical_spacing=0.1)

    fig.add_trace(go.Scatter(x=delta["Distance"], y=delta["Speed_VER"], name="VER", line=dict(color="#1e90ff")), row=1, col=1)
    fig.add_trace(go.Scatter(x=delta["Distance"], y=delta["Speed_LEC"], name="LEC", line=dict(color="#dc0000")), row=1, col=1)

    fig.add_trace(go.Scatter(x=delta["Distance"], y=delta["Delta"], name="Delta", line=dict(color="orange"), showlegend=False), row=2, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)

    fig.update_xaxes(title_text="Distance (m)", row=2, col=1)
    fig.update_yaxes(title_text="Speed (km/h)", row=1, col=1)
    fig.update_yaxes(title_text="Delta (s)", row=2, col=1)
    fig.update_layout(height=600, title_text="Lap Comparison")
    return fig

def build_corner_ranking_fig(corner_rank):
    colors = ["#1e90ff" if w == "VER" else "#dc0000" for w in corner_rank["winner"]]
    fig = go.Figure(go.Bar(
        x=[f"Corner {int(c)}" for c in corner_rank["corner_number"]],
        y=corner_rank["delta_swing"],
        marker_color=colors,
        text=corner_rank["winner"],
        textposition="outside"
    ))
    fig.update_layout(title="Corner Ranking by Time Impact", xaxis_title="Corner", yaxis_title="Delta Swing (s)", height=400)
    return fig

def build_strategy_fig(mc_results):
    mc_results["label"] = mc_results["compound_1"] + "→" + mc_results["compound_2"] + " (lap " + mc_results["pit_lap"].astype(str) + ")"
    top10 = mc_results.nsmallest(10, "mean_total_time")

    fig = go.Figure(go.Bar(
        x=top10["mean_total_time"],
        y=top10["label"],
        orientation="h",
        marker_color="#00d2be",
        error_x=dict(type="data", array=(top10["p90"] - top10["mean_total_time"]))
    ))
    fig.update_layout(title="Top 10 Pit Strategies (Monte Carlo, Bahrain 2024)",
                       xaxis_title="Predicted Race Time (s)", height=500)
    fig.update_xaxes(range=[top10["mean_total_time"].min() - 5, top10["mean_total_time"].max() + 5])
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
    fig.update_layout(title="Pit Stop Optimizer Recommendations", height=300)
    return fig

if __name__ == "__main__":
    delta, corner_rank, mc_results, pit_rec = load_data()

    figs = [
        build_lap_comparison_fig(delta),
        build_corner_ranking_fig(corner_rank),
        build_strategy_fig(mc_results),
        build_pit_recommendation_table(pit_rec)
    ]

    with open(OUTPUT_PATH, "w") as f:
        f.write("<html><head><title>F1 Telemetry & Strategy Dashboard</title>")
        f.write("<style>body{font-family:Arial;background:#f5f5f5;margin:20px;} h1{color:#1a1a2e;}</style>")
        f.write("</head><body>")
        f.write("<h1>F1 Telemetry & Strategy Dashboard</h1>")
        f.write("<p>Bahrain Grand Prix 2024 — VER vs LEC telemetry, race strategy simulation</p>")
        for fig in figs:
            f.write(pio.to_html(fig, full_html=False, include_plotlyjs="cdn"))
        f.write("</body></html>")

    print(f"Dashboard saved to {OUTPUT_PATH}")