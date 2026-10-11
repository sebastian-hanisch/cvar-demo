"""Plotly-Figuren: Kostenverteilung beider Pläne, Pareto-Kurve, Pläne je Standort, Experiment. Alle Achsen fest (fixedrange)."""

import numpy as np
import plotly.graph_objects as go

import cvr_constants as C


def _fixed(fig, height=340):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.24))
    return fig


def build_distribution(mean_plan, risk_plan, alpha) -> go.Figure:
    """Gesamtkosten beider Pläne über die Referenzszenarien (je 600 gleich wahrscheinlich), mit Mittel und CVaR."""
    lo = min(min(mean_plan.costs), min(risk_plan.costs))
    hi = max(max(mean_plan.costs), max(risk_plan.costs))
    bins = dict(start=lo, end=hi, size=(hi - lo) / 40.0)
    fig = go.Figure()
    for name, pv, color in (("Mittelwertplan", mean_plan, C.COLOR_MEAN_PLAN), ("Risikoplan", risk_plan, C.COLOR_RISK_PLAN)):
        fig.add_trace(go.Histogram(x=list(pv.costs), xbins=bins, name=name, marker_color=color, opacity=0.6, histnorm="percent"))
        fig.add_vline(x=pv.mean, line_color=color, line_dash="dot")
        fig.add_vline(x=pv.cvar, line_color=color, line_dash="dash")
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(title=f"Gesamtkosten je Szenario (gepunktet: Mittel, gestrichelt: CVaR {int(round(alpha * 100))} %)")
    fig.update_yaxes(title="% der Szenarien")
    return _fixed(fig, 360)


def build_frontier(frontier, selected_lam) -> go.Figure:
    """Pareto-Kurve: Erwartungswert gegen CVaR der Kosten je Gewicht lam, aus derselben Stichprobe, auf der Referenz ausgewertet."""
    xs = [p[1] for p in frontier]
    ys = [p[2] for p in frontier]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers+text", text=[f"λ = {str(p[0]).replace('.', ',')}" for p in frontier],
                             textposition="top right", line=dict(color=C.COLOR_FRONTIER), marker=dict(size=9), showlegend=False,
                             hovertemplate="Mittel %{x:.1f}<br>CVaR %{y:.1f}<extra></extra>"))
    sel = [p for p in frontier if p[0] == selected_lam]
    if sel:
        fig.add_trace(go.Scatter(x=[sel[0][1]], y=[sel[0][2]], mode="markers", name="gewähltes Gewicht",
                                 marker=dict(size=16, color=C.COLOR_RISK_PLAN, symbol="diamond-open", line=dict(width=3))))
    fig.update_xaxes(title="Erwartungswert der Kosten (Referenz)", range=[min(xs) - 0.05 * (max(xs) - min(xs) + 1), max(xs) + 0.25 * (max(xs) - min(xs) + 1)])
    fig.update_yaxes(title="CVaR der Kosten (Referenz)")
    return _fixed(fig, 340)


def build_plans(mu, x_mean, x_risk) -> go.Figure:
    names = [f"Standort {i + 1}" for i in range(len(mu))]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=list(mu), name="mittlere Nachfrage", marker_color=C.COLOR_GRID))
    fig.add_trace(go.Bar(x=names, y=list(x_mean), name="Mittelwertplan", marker_color=C.COLOR_MEAN_PLAN))
    fig.add_trace(go.Bar(x=names, y=list(x_risk), name="Risikoplan", marker_color=C.COLOR_RISK_PLAN))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="Kapazität")
    return _fixed(fig)


def build_experiment(rows) -> go.Figure:
    s = [r["s"] for r in rows]
    fig = go.Figure()
    for key, name, color in (("mean", "Mittelwertplan (Regret im Erwartungswert)", C.COLOR_MEAN_PLAN),
                             ("risk", "Risikoplan (Regret im gemischten Ziel)", C.COLOR_RISK_PLAN)):
        fig.add_trace(go.Scatter(
            x=s, y=[max(r[f"regret_{key}"], 1e-3) for r in rows], mode="lines+markers", name=name, line=dict(color=color),
            error_y=dict(type="data", symmetric=False, array=[max(r[f"regret_{key}_p90"] - r[f"regret_{key}"], 0.0) for r in rows],
                         arrayminus=[0.0 for _ in rows], thickness=1, width=3)))
    fig.update_xaxes(title="Szenarienzahl der Stichprobe", type="log", tickvals=s, ticktext=[str(v) for v in s])
    fig.update_yaxes(title="mittlerer Regret in % (Balken: 90. Perzentil)", type="log")
    return _fixed(fig, 360)
