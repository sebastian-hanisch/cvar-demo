"""Kennzahlen: Mittelwert- und Risikoplan aus einer Stichprobe, ausgewertet auf einer bekannten Referenzverteilung; Pareto-Kurve; Experiment.

Die Referenzverteilung besteht aus REF_SCENARIOS gleich wahrscheinlichen Szenarien; eine Stichprobe sind S Ziehungen mit Zurücklegen daraus.
Das Risikomaß ist CVaR_alpha der GESAMTkosten (Vorhaltung plus Stufe 2), das Gewicht lam mischt es mit dem Erwartungswert:
    Ziel = (1 - lam) E[Kosten] + lam CVaR_alpha[Kosten]"""

from dataclasses import dataclass

import numpy as np

import cvr_algorithm as A
import cvr_constants as C
from cvr_cvar import PlanValue, evaluate_plan, solve_risk
from cvr_rng import uniform_block
from cvr_scenario import Instance, demand_scenarios, make_instance


@dataclass(frozen=True)
class Settings:
    s: int = C.DEFAULT_S
    sigma: float = C.DEFAULT_SIGMA
    lam: float = C.DEFAULT_LAMBDA
    alpha: float = C.DEFAULT_ALPHA
    budget: str = C.DEFAULT_BUDGET
    transfer: str = C.DEFAULT_TRANSFER
    seed: int = C.DEFAULT_SEED
    draw: int = C.DEFAULT_DRAW


@dataclass(frozen=True)
class Analysis:
    inst: Instance
    x_mean: tuple[float, ...]
    x_risk: tuple[float, ...]
    mean_plan: PlanValue         # Mittelwertplan, auf der Referenz ausgewertet
    risk_plan: PlanValue         # Risikoplan, auf der Referenz ausgewertet
    mean_change_pct: float       # Mittelwert der Kosten: Risikoplan gegen Mittelwertplan
    cvar_change_pct: float       # CVaR der Kosten: Risikoplan gegen Mittelwertplan
    frontier: tuple              # ((lam, mean, cvar), ...) aus derselben Stichprobe, auf der Referenz
    verdict: str                 # 'kein_unterschied' | 'tausch' | 'nur_kosten'


def build_instance(settings: Settings) -> Instance:
    ratio = C.BUDGET_TIGHT if settings.budget == "knapp" else C.BUDGET_FREE
    return make_instance(
        settings.seed, sigma=settings.sigma, rho=C.RHO, budget_ratio=ratio,
        spot_mult=C.SPOT_MULT, transfer=settings.transfer == "an",
    )


def reference_demand(inst: Instance) -> np.ndarray:
    demand, _ = demand_scenarios(inst, C.REF_SEED, count=C.REF_SCENARIOS)
    return demand


def sample_scenarios(demand: np.ndarray, seed: int, s: int) -> np.ndarray:
    """S Ziehungen MIT Zurücklegen aus den gleich wahrscheinlichen Szenarien der Referenzverteilung (Form (s, J))."""
    idx = np.minimum((uniform_block(seed, s) * len(demand)).astype(int), len(demand) - 1)
    return demand[idx]


def draw_seed(base: int, k: int, s: int) -> int:
    return 1_000_003 * int(base) + 7919 * int(k) + 17 * int(s) + 11


def blend(pv: PlanValue, lam: float) -> float:
    """Zielwert (1 - lam) Mittel + lam CVaR eines ausgewerteten Plans."""
    return (1.0 - lam) * pv.mean + lam * pv.cvar


def verdict_of(mean_change: float, cvar_change: float) -> str:
    if abs(cvar_change) < 2.0 and abs(mean_change) < 1.0:
        return "kein_unterschied"
    if cvar_change <= -2.0:
        return "tausch"
    return "nur_kosten"


def analyse(settings: Settings) -> Analysis:
    inst = build_instance(settings)
    ref = reference_demand(inst)
    sample = sample_scenarios(ref, draw_seed(settings.draw, 0, settings.s), settings.s)
    x_mean, _ = solve_risk(inst, sample, settings.alpha, 0.0)
    x_risk, _ = solve_risk(inst, sample, settings.alpha, settings.lam) if settings.lam > 0 else (x_mean, 0.0)
    pv_mean = evaluate_plan(inst, x_mean, ref, settings.alpha)
    pv_risk = pv_mean if settings.lam == 0 else evaluate_plan(inst, x_risk, ref, settings.alpha)
    frontier = []
    for lam in C.LAMBDA_GRID:
        if lam == 0.0:
            pv = pv_mean
        elif lam == settings.lam:
            pv = pv_risk
        else:
            x, _ = solve_risk(inst, sample, settings.alpha, lam)
            pv = evaluate_plan(inst, x, ref, settings.alpha)
        frontier.append((lam, pv.mean, pv.cvar))
    mean_change = 100.0 * (pv_risk.mean / pv_mean.mean - 1.0)
    cvar_change = 100.0 * (pv_risk.cvar / pv_mean.cvar - 1.0)
    return Analysis(
        inst, tuple(float(v) for v in x_mean), tuple(float(v) for v in x_risk), pv_mean, pv_risk,
        mean_change, cvar_change, tuple(frontier), verdict_of(mean_change, cvar_change),
    )


def experiment(settings: Settings, progress=None) -> list[dict]:
    """Je Szenarienzahl DRAWS Ziehungen: relativer Regret von Mittelwert- und Risikoplan in IHREM eigenen Ziel gegen den Referenzplan."""
    inst = build_instance(settings)
    ref = reference_demand(inst)
    lam, alpha = settings.lam, settings.alpha
    x_ref_mean, _ = solve_risk(inst, ref, alpha, 0.0)
    x_ref_risk, _ = solve_risk(inst, ref, alpha, lam)
    obj_ref_mean = blend(evaluate_plan(inst, x_ref_mean, ref, alpha), 0.0)
    obj_ref_risk = blend(evaluate_plan(inst, x_ref_risk, ref, alpha), lam)
    rows, done, total = [], 0, len(C.SWEEP_S) * C.DRAWS
    for s in C.SWEEP_S:
        reg_mean, reg_risk, dev_mean, dev_risk = [], [], [], []
        for k in range(C.DRAWS):
            sample = sample_scenarios(ref, draw_seed(settings.draw, k, s), s)
            x_m, _ = solve_risk(inst, sample, alpha, 0.0)
            x_r, _ = solve_risk(inst, sample, alpha, lam)
            reg_mean.append(100.0 * (blend(evaluate_plan(inst, x_m, ref, alpha), 0.0) / obj_ref_mean - 1.0))
            reg_risk.append(100.0 * (blend(evaluate_plan(inst, x_r, ref, alpha), lam) / obj_ref_risk - 1.0))
            dev_mean.append(100.0 * float(np.abs(x_m - x_ref_mean).sum()) / float(x_ref_mean.sum()))
            dev_risk.append(100.0 * float(np.abs(x_r - x_ref_risk).sum()) / float(x_ref_risk.sum()))
            done += 1
            if progress is not None:
                progress(done / total)
        rows.append({
            "s": s, "regret_mean": float(np.mean(reg_mean)), "regret_risk": float(np.mean(reg_risk)),
            "regret_mean_p90": float(np.percentile(reg_mean, 90)), "regret_risk_p90": float(np.percentile(reg_risk, 90)),
            "dev_mean": float(np.mean(dev_mean)), "dev_risk": float(np.mean(dev_risk)),
        })
    return rows
