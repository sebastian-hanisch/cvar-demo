"""Jede Aussage aus README und App-Text wird hier nachgerechnet (Bänder statt exakter Werte: CI installiert die neuesten numpy/scipy)."""

import pytest

import cvr_constants as C
import cvr_evaluation as ev


@pytest.fixture(scope="module")
def presets():
    return {name: ev.analyse(ev.Settings(**p)) for name, p in C.PRESETS.items()}


def test_default_trades_mean_for_tail(presets):
    a = presets["Standardfall (Voreinstellung)"]
    assert a.verdict == "tausch"
    assert 12.0 <= a.mean_change_pct <= 25.0
    assert -25.0 <= a.cvar_change_pct <= -15.0


def test_pure_tail_focus_costs_more_in_the_mean_for_a_similar_tail(presets):
    a, b = presets["Standardfall (Voreinstellung)"], presets["Nur den Schwanz im Blick"]
    assert b.mean_change_pct > a.mean_change_pct + 5.0
    assert abs(b.cvar_change_pct - a.cvar_change_pct) < 3.0       # der Schwanz gewinnt kaum noch etwas dazu


def test_tight_budget_makes_the_risk_measure_almost_irrelevant(presets):
    a = presets["Knappes Budget: Risiko ändert kaum etwas"]
    assert a.verdict == "kein_unterschied"
    assert abs(a.mean_change_pct) < 1.0 and abs(a.cvar_change_pct) < 2.0
    assert sum(a.x_risk) == pytest.approx(a.inst.budget, rel=1e-6)


def test_the_frontier_is_ordered_in_lambda_and_overfits_at_the_extreme(presets):
    f = presets["Standardfall (Voreinstellung)"].frontier
    means = [p[1] for p in f]
    cvars = [p[2] for p in f]
    assert means == sorted(means)
    assert cvars[2] < cvars[1] < cvars[0]
    # dieselbe Ziehung: das Gewicht 0,75 hat auf der Referenz einen niedrigeren CVaR als das Gewicht 1 (der reine CVaR-Plan überpasst den Schwanz der 100 Szenarien)
    assert cvars[3] < cvars[4]


def test_few_scenarios_give_a_larger_mean_price_for_the_same_tail(presets):
    few = presets["Wenige Szenarien"]
    assert few.verdict == "tausch"
    assert few.mean_change_pct < presets["Nur den Schwanz im Blick"].mean_change_pct


def test_a_deeper_tail_costs_more():
    changes = [ev.analyse(ev.Settings(lam=1.0, alpha=a)).mean_change_pct for a in C.ALPHA_CHOICES]
    assert changes == sorted(changes)
    assert changes[-1] > changes[0] + 10.0


def test_small_spread_shrinks_both_effects():
    low = ev.analyse(ev.Settings(sigma=0.1, lam=1.0))
    high = ev.analyse(ev.Settings(sigma=0.35, lam=1.0))
    assert low.mean_change_pct < high.mean_change_pct
    assert abs(low.cvar_change_pct) < abs(high.cvar_change_pct)


@pytest.fixture(scope="module")
def rows():
    return {r["s"]: r for r in ev.experiment(ev.Settings(lam=1.0))}


def test_the_risk_plan_needs_about_ten_times_the_scenarios(rows):
    for s, r in rows.items():
        assert r["regret_risk"] >= 3 * r["regret_mean"], s
    assert rows[200]["regret_risk"] <= 1.6 * rows[20]["regret_mean"]
    assert rows[100]["regret_risk"] > rows[20]["regret_mean"]


def test_the_risk_plan_moves_more_between_draws(rows):
    for r in rows.values():
        assert r["dev_risk"] > 1.5 * r["dev_mean"]
    assert rows[20]["regret_risk"] > rows[200]["regret_risk"]
