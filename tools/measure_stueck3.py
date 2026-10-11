"""Messreihe für README und tests/test_claims.py (Python: _venvs/test). Gibt alle Zahlen aus, die im README stehen."""

import sys
import time
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cvr_constants as C  # noqa: E402
import cvr_evaluation as ev  # noqa: E402


def main():
    print("== Presets (Seed 7, Ziehung 1)")
    for name, p in C.PRESETS.items():
        a = ev.analyse(ev.Settings(**p))
        print(f"{name:<44} dE {a.mean_change_pct:+6.2f} % dCVaR {a.cvar_change_pct:+6.2f} % -> {a.verdict}; Mittelwertplan E {a.mean_plan.mean:.1f} "
              f"CVaR {a.mean_plan.cvar:.1f}; Risikoplan E {a.risk_plan.mean:.1f} CVaR {a.risk_plan.cvar:.1f}")
        print("   Pareto:", [(l, round(m, 1), round(c, 1)) for l, m, c in a.frontier])
    print("== Lambda-Reihe (frei, Voreinstellung), Median über 5 Ziehungen")
    for lam in (0.25, 0.5, 0.75, 1.0):
        runs = [ev.analyse(ev.Settings(lam=lam, draw=d)) for d in range(1, 6)]
        print(f"lam {lam}: dE {median(r.mean_change_pct for r in runs):+.1f} % dCVaR {median(r.cvar_change_pct for r in runs):+.1f} % "
              f"Opfer je Prozent {median(r.mean_change_pct / -r.cvar_change_pct for r in runs):.2f}")
    print("== alpha-Reihe (lam 1)")
    for alpha in C.ALPHA_CHOICES:
        a = ev.analyse(ev.Settings(lam=1.0, alpha=alpha))
        print(f"alpha {alpha}: dE {a.mean_change_pct:+.1f} % dCVaR {a.cvar_change_pct:+.1f} %")
    print("== sigma 0,1, lam 1")
    a = ev.analyse(ev.Settings(sigma=0.1, lam=1.0))
    print(f"dE {a.mean_change_pct:+.1f} % dCVaR {a.cvar_change_pct:+.1f} %")
    print("== Experiment (Voreinstellung mit lam 1)")
    t = time.time()
    for r in ev.experiment(ev.Settings(lam=1.0)):
        print({k: round(v, 2) for k, v in r.items()})
    print("Dauer", round(time.time() - t), "s")


if __name__ == "__main__":
    main()
