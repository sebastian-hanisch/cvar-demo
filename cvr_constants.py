"""Konstanten: Vehikel (wie in der Wurzel der Linie), Regler-Grenzen, Experiment, Farben und Presets."""

# --- Vehikel: Kapazitätsvorhaltung mit Zukauf, Umlagerung und Fehlmenge (identisch zur Wurzel der Linie) --------------------------------------
J = 6
MU_LOW, MU_HIGH = 60, 140
CAP_COST = 1.0
SPOT_JITTER = 0.1
UNMET_MULT = 3.0
SPOT_LIMIT = 0.5
TRANSFER_BASE, TRANSFER_SCALE = 0.3, 0.35
Z0_BINS = 5                     # nur für die Kopie des Kerns
SCENARIOS = 200                 # Vorgabe von `demand_scenarios`, hier unbenutzt
RHO = 0.4
SPOT_MULT = 1.9
SCENARIO_SEED_OFFSET = 7_000_003
BUDGET_TIGHT = 0.95             # „knapp“: Summe der Kapazitäten höchstens 95 % der mittleren Gesamtnachfrage
BUDGET_FREE = 10.0              # „frei“: so weit, dass es nie bindet

# --- Die „wahre“ Verteilung: eine große Referenzmenge (die Demo misst nur gegen sie) ---------------------------------------------------------
REF_SCENARIOS = 600             # durch 20 teilbar: (1 - alpha) * 600 ist für alpha in {0,8; 0,9; 0,95} ganzzahlig (60, 30, ...)
REF_SEED = 900_001

# --- Regler --------------------------------------------------------------------------------------------------------------------------------
S_MIN, S_MAX, S_STEP, DEFAULT_S = 20, 300, 20, 100
SIGMA_MIN, SIGMA_MAX, SIGMA_STEP, DEFAULT_SIGMA = 0.10, 0.60, 0.05, 0.35
LAMBDA_MIN, LAMBDA_MAX, LAMBDA_STEP, DEFAULT_LAMBDA = 0.0, 1.0, 0.25, 0.5
ALPHA_CHOICES = (0.8, 0.9, 0.95)
DEFAULT_ALPHA = 0.9
BUDGET_CHOICES = ("frei", "knapp")
DEFAULT_BUDGET = "frei"
TRANSFER_CHOICES = ("an", "aus")
DEFAULT_TRANSFER = "an"
SEED_MAX, DEFAULT_SEED = 999999, 7
DRAW_MAX, DEFAULT_DRAW = 999, 1

# --- Experiment ----------------------------------------------------------------------------------------------------------------------------
LAMBDA_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)   # Pareto-Kurve
SWEEP_S = (20, 50, 100, 200)
DRAWS = 16                                  # unabhängige Ziehungen je Szenarienzahl

# --- Farben --------------------------------------------------------------------------------------------------------------------------------
COLOR_MEAN_PLAN = "#B5651D"
COLOR_RISK_PLAN = "#2F6B65"
COLOR_FRONTIER = "#4c78a8"
COLOR_GRID = "rgba(150,150,150,0.75)"

PRESETS = {
    "Standardfall (Voreinstellung)": {
        "s": DEFAULT_S, "sigma": DEFAULT_SIGMA, "lam": DEFAULT_LAMBDA, "alpha": DEFAULT_ALPHA,
        "budget": DEFAULT_BUDGET, "transfer": DEFAULT_TRANSFER, "seed": DEFAULT_SEED, "draw": DEFAULT_DRAW,
    },
    "Nur den Tail im Blick": {
        "s": DEFAULT_S, "sigma": DEFAULT_SIGMA, "lam": 1.0, "alpha": DEFAULT_ALPHA,
        "budget": DEFAULT_BUDGET, "transfer": DEFAULT_TRANSFER, "seed": DEFAULT_SEED, "draw": DEFAULT_DRAW,
    },
    "Knappes Budget: Risiko ändert kaum etwas": {
        "s": DEFAULT_S, "sigma": DEFAULT_SIGMA, "lam": 1.0, "alpha": DEFAULT_ALPHA,
        "budget": "knapp", "transfer": DEFAULT_TRANSFER, "seed": DEFAULT_SEED, "draw": DEFAULT_DRAW,
    },
    "Wenige Szenarien": {
        "s": 20, "sigma": DEFAULT_SIGMA, "lam": 1.0, "alpha": DEFAULT_ALPHA,
        "budget": DEFAULT_BUDGET, "transfer": DEFAULT_TRANSFER, "seed": DEFAULT_SEED, "draw": DEFAULT_DRAW,
    },
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "Gewicht 0,5 auf den Tail (CVaR, 90 %), Kapazität frei, 100 Szenarien, Streuung 35 %.",
    "Nur den Tail im Blick": "Gewicht 1: der Plan minimiert nur die Kosten der schlimmsten 10 % der Szenarien.",
    "Knappes Budget: Risiko ändert kaum etwas": "Das Budget bindet, es wird nur verteilt: der Risikoplan unterscheidet sich kaum vom Mittelwertplan.",
    "Wenige Szenarien": "Nur 20 Szenarien: der Tail besteht aus zwei Szenarien, der Risikoplan streut stark.",
}
