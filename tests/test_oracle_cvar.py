"""Orakel-Tests (DEMO-PLAYBOOK §12): anderer Rechenweg als der Kern.

1. Dasselbe Risikoproblem als eigenes LP in OR-Tools (GLOP, Schleifen statt Blockmatrizen), Rockafellar/Uryasev mit eigener Indizierung.
2. CVaR einer Stichprobe gegen die Definition als Minimum über eta (Auswertung an allen Stichprobenwerten), nicht gegen Sortieren.
3. Der Risikoplan unterbietet jeden Zufallsplan im gemischten Ziel (kein Plan darf besser sein als das LP-Optimum)."""

import dataclasses

import numpy as np
import pytest

import cvr_evaluation as ev
import cvr_scenario as S
from cvr_cvar import cvar_of, evaluate_plan, solve_risk

pywraplp = pytest.importorskip("ortools.linear_solver.pywraplp")


def _glop_risk_value(inst, demand, alpha, lam) -> float:
    j_count, s_count = inst.n, demand.shape[0]
    solver = pywraplp.Solver.CreateSolver("GLOP")
    inf = solver.infinity()
    x = [solver.NumVar(0, inf, f"x{j}") for j in range(j_count)]
    eta = solver.NumVar(-inf, inf, "eta")
    z = [solver.NumVar(0, inf, f"z{s}") for s in range(s_count)]
    solver.Add(sum(x) <= inst.budget)
    obj = solver.Objective()
    for j in range(j_count):
        obj.SetCoefficient(x[j], inst.cap_cost)
    obj.SetCoefficient(eta, lam)
    for s in range(s_count):
        q_terms = []
        y = {}
        for j in range(j_count):
            for k in range(j_count):
                y[j, k] = solver.NumVar(0, inf if (inst.transfer or j == k) else 0.0, f"y{s}_{j}_{k}")
                q_terms.append((y[j, k], inst.transfer_cost[j][k]))
        for k in range(j_count):
            u = solver.NumVar(0, inst.spot_limit[k], f"u{s}_{k}")
            w = solver.NumVar(0, inf, f"w{s}_{k}")
            q_terms.append((u, inst.spot[k]))
            q_terms.append((w, inst.unmet))
            solver.Add(sum(y[j, k] for j in range(j_count)) + u + w == float(demand[s, k]))
        for j in range(j_count):
            solver.Add(sum(y[j, k] for k in range(j_count)) <= x[j])
        solver.Add(sum(c * v for v, c in q_terms) - eta - z[s] <= 0)
        for v, c in q_terms:
            obj.SetCoefficient(v, obj.GetCoefficient(v) + (1 - lam) * c / s_count)
        obj.SetCoefficient(z[s], lam / ((1 - alpha) * s_count))
    obj.SetMinimization()
    assert solver.Solve() == pywraplp.Solver.OPTIMAL
    return obj.Value()


@pytest.mark.parametrize("transfer", [True, False])
@pytest.mark.parametrize("lam", [0.3, 1.0])
def test_risk_lp_matches_independent_glop_model(transfer, lam):
    inst = dataclasses.replace(
        S.make_instance(41, sigma=0.4, rho=0.4, budget_ratio=0.9, spot_mult=1.6, transfer=transfer),
        mu=(80.0, 120.0, 100.0), spot=(1.7, 1.5, 1.9), spot_limit=(40.0, 60.0, 50.0),
        transfer_cost=((0.0, 0.3, 0.5), (0.3, 0.0, 0.4), (0.5, 0.4, 0.0)), budget=1e9,
    )
    ref = ev.reference_demand(inst)
    sample = ev.sample_scenarios(ref, 3, 20)
    value = solve_risk(inst, sample, 0.9, lam)[1]
    assert value == pytest.approx(_glop_risk_value(inst, sample, 0.9, lam), rel=1e-7)


@pytest.mark.parametrize("alpha", [0.5, 0.8, 0.9])
def test_cvar_matches_the_minimisation_definition(alpha):
    rng = np.random.default_rng(7)
    v = rng.gamma(2.0, 20.0, 50)
    n = len(v)
    # CVaR = min_eta { eta + E[(v - eta)+] / (1 - alpha) }: das Minimum liegt an einem der Stichprobenwerte
    definition = min(eta + np.mean(np.maximum(v - eta, 0.0)) / (1 - alpha) for eta in v)
    assert cvar_of(v, alpha) == pytest.approx(definition, rel=1e-9)
    assert n == 50


def test_no_random_plan_beats_the_risk_optimum():
    settings = ev.Settings(s=40, lam=0.5)
    inst = ev.build_instance(settings)
    sample = ev.sample_scenarios(ev.reference_demand(inst), 11, 40)
    x_opt, obj = solve_risk(inst, sample, 0.9, 0.5)
    rng = np.random.default_rng(2)
    for _ in range(40):
        x = np.asarray(inst.mu) * rng.uniform(0.4, 1.6, inst.n)
        pv = evaluate_plan(inst, x, sample, 0.9)
        assert 0.5 * pv.mean + 0.5 * pv.cvar >= obj - 1e-6
