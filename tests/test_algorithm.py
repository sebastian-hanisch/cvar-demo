"""Einheiten: CVaR-Berechnung, Risiko-LP an der Mini-Instanz, Auswertung eines Plans; Ergebnisse von Hand gerechnet."""

import numpy as np
import pytest

import cvr_algorithm as A
import cvr_constants as C
import cvr_evaluation as ev
from cvr_cvar import cvar_of, evaluate_plan, solve_risk, stage2_costs


def test_cvar_of_hand_values():
    v = [1.0, 2.0, 3.0, 4.0, 10.0, 20.0, 30.0, 40.0, 50.0, 100.0]
    assert cvar_of(v, 0.9) == pytest.approx(100.0)               # teuerstes Zehntel = ein Wert
    assert cvar_of(v, 0.8) == pytest.approx(75.0)                # zwei teuerste: (100 + 50) / 2
    assert cvar_of(v, 0.0) == pytest.approx(np.mean(v))          # alpha = 0: das Mittel
    assert cvar_of(v, 0.85) == pytest.approx((100 + 50 * 0.5) / 1.5)   # k = 1,5: ein Wert plus halber zweiter, geteilt durch 1,5


def test_cvar_is_order_independent_and_at_least_the_mean():
    rng = np.random.default_rng(3)
    v = rng.uniform(0, 100, 40)
    assert cvar_of(v, 0.9) == pytest.approx(cvar_of(rng.permutation(v), 0.9))
    assert cvar_of(v, 0.9) >= v.mean() - 1e-9


def test_stage2_costs_hand_values(mini, mini_no_transfer):
    d = np.array([[100.0, 50.0], [60.0, 60.0]])
    q = stage2_costs(mini, d, np.array([80.0, 80.0]))
    assert q[0] == pytest.approx(10.0)       # 20 Einheiten umgelagert zu 0,5
    assert q[1] == pytest.approx(0.0)        # Nachfrage 60 + 60 liegt unter der Kapazität
    q_off = stage2_costs(mini_no_transfer, d, np.array([80.0, 80.0]))
    assert q_off[0] == pytest.approx(40.0)   # 20 Einheiten Zukauf zu 2


def test_lambda_zero_is_the_expected_value_problem(mini):
    d = np.array([[100.0, 50.0], [70.0, 90.0], [120.0, 40.0], [60.0, 60.0]])
    x, obj = solve_risk(mini, d, alpha=0.5, lam=0.0)
    ref, x_ref = A.solve_grouped(mini, d, np.zeros(4, dtype=int))
    assert obj == pytest.approx(ref, rel=1e-8)
    assert evaluate_plan(mini, x, d, 0.5).mean == pytest.approx(ref, rel=1e-8)


def test_objective_equals_mixture_of_mean_and_cvar_of_total_costs(mini):
    d = np.array([[100.0, 50.0], [70.0, 90.0], [120.0, 40.0], [60.0, 60.0], [90.0, 70.0], [50.0, 100.0]])
    for lam in (0.25, 0.5, 1.0):
        x, obj = solve_risk(mini, d, alpha=0.5, lam=lam)
        pv = evaluate_plan(mini, x, d, 0.5)
        assert obj == pytest.approx((1 - lam) * pv.mean + lam * pv.cvar, rel=1e-7)


def test_risk_plan_is_never_worse_in_its_own_objective(mini):
    d = np.array([[100.0, 50.0], [70.0, 90.0], [120.0, 40.0], [60.0, 60.0], [90.0, 70.0], [50.0, 100.0]])
    alpha, lam = 0.5, 0.5
    x_mean, _ = solve_risk(mini, d, alpha, 0.0)
    x_risk, obj = solve_risk(mini, d, alpha, lam)
    pv_mean = evaluate_plan(mini, x_mean, d, alpha)
    assert obj <= (1 - lam) * pv_mean.mean + lam * pv_mean.cvar + 1e-7


def test_tight_budget_binds_and_risk_changes_little():
    inst_tight = ev.build_instance(ev.Settings(budget="knapp"))
    d = ev.sample_scenarios(ev.reference_demand(inst_tight), 5, 40)
    x, _ = solve_risk(inst_tight, d, 0.9, 1.0)
    assert x.sum() <= inst_tight.budget + 1e-6
    assert x.sum() == pytest.approx(inst_tight.budget, rel=1e-6)     # knapp: das Budget bindet


def test_sampling_is_deterministic_and_seeds_are_distinct():
    ref = np.arange(30, dtype=float).reshape(10, 3)
    a = ev.sample_scenarios(ref, 5, 7)
    assert np.array_equal(a, ev.sample_scenarios(ref, 5, 7)) and a.shape == (7, 3)
    seeds = {ev.draw_seed(b, k, s) for b in range(4) for k in range(4) for s in (20, 50)}
    assert len(seeds) == 32 and C.REF_SEED not in seeds


def test_reference_size_makes_every_tail_size_integral():
    for alpha in C.ALPHA_CHOICES:
        k = (1 - alpha) * C.REF_SCENARIOS
        assert k == pytest.approx(round(k))
