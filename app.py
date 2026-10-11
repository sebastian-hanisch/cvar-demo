"""Risiko als Ziel: Erwartungswert und CVaR - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import cvr_constants as C
from cvr_evaluation import Settings, analyse, build_instance, experiment
from cvr_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    new_draw,
    randomize_seed,
    sync_query_params,
)
from cvr_visualization import build_distribution, build_experiment, build_frontier, build_plans

st.set_page_config(page_title="Risiko als Ziel – Sebastian Hanisch", layout="wide")


def _de(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def _pct(value: float, digits: int = 1) -> str:
    return f"{value:+.{digits}f} %".replace(".", ",").replace("-", "−")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _experiment(settings):
    return experiment(settings)


st.title("🛡️ Risiko als Ziel: Erwartungswert und CVaR")
st.markdown(
    """
Ein Plan, der **im Mittel** am billigsten ist, kann in den **schlechtesten Szenarien** sehr teuer werden. Der **CVaR** (Conditional Value at Risk) ist das Mittel der
teuersten 10 oder 20 % der Szenarien. Diese Demo fragt: **Was kostet es, den Tail zu drücken, und lohnt es sich?** Dazu mischt sie Mittelwert und CVaR mit
einem Gewicht λ und zeigt, wie sich Kosten und Tail zueinander verhalten.

Anders als die Fall-Demos zeigt sie **ein** Verfahren an einem wachsenden Beispiel, mit demselben Kapazitäts-Vehikel wie die
[Wurzel der Linie](https://github.com/sebastian-hanisch/newsvendor-evpi-demo) und die Stichproben-Demo davor; die Szenarien kommen hier aus einer Stichprobe.
Weiter unten: das Experiment zum Szenarienbedarf, **🚧 Wo die Annahmen enden** und **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert die Optimierung auf den CVaR", expanded=True):
    st.markdown(
        """
1. **Szenarien:** S Nachfrage-Szenarien aus der Verteilung (Stichprobe, wie in der Stichproben-Demo der Linie).
2. **Zielfunktion:** Gesamtkosten (Vorhaltung plus Stufe 2). Der **Mittelwertplan** minimiert deren Mittel. Der **Risikoplan** minimiert
   (1 − λ) · Mittel + λ · CVaR, den CVaR der teuersten (1 − α)-Anteile der Szenarien.
3. **Als LP:** Der CVaR lässt sich mit einer Hilfsvariablen η und je Szenario einer Überschreitung z_s linear ausdrücken (Rockafellar und Uryasev),
   so bleibt alles ein lineares Programm.
4. **Prüfen:** beide Pläne auf einer großen Referenzmenge von 600 Szenarien (die Verteilung): Mittel und CVaR der wahren Kosten.
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    cols = st.columns(len(C.PRESETS))
    for col, name in zip(cols, C.PRESETS):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Risiko**")
    lam = st.slider("Gewicht λ auf den CVaR", *bounds("lam_slider"), step=C.LAMBDA_STEP, key="lam_slider",
                    help="0: nur der Erwartungswert (Mittelwertplan). 1: nur der CVaR. Dazwischen die Mischung.")
    alpha = st.radio("Tail: teuerste Szenarien", C.ALPHA_CHOICES, key="alpha_radio", horizontal=True,
                     format_func=lambda a: f"{round((1 - a) * 100)} %",
                     help="Welcher Anteil der teuersten Szenarien in den CVaR eingeht.")
    st.markdown("**Stichprobe**")
    s = st.slider("Szenarienzahl S der Stichprobe", *bounds("s_slider"), step=C.S_STEP, key="s_slider",
                  help="Wie viele Szenarien die Pläne sehen. Der Tail besteht aus (1 − α) · S Szenarien.")
    draw = st.number_input("Ziehung (Zufalls-Seed der Stichprobe)", *bounds("draw_input"), key="draw_input", step=1)
    st.button("🎲 Neue Ziehung", width="stretch", on_click=new_draw)
    st.markdown("**Nachfrage und Möglichkeiten**")
    sigma = st.slider("Streuung (Log-Streuung σ)", *bounds("sigma_slider"), step=C.SIGMA_STEP, key="sigma_slider",
                      help="Wie stark die Nachfrage um ihren Mittelwert schwankt.")
    budget = st.radio("Kapazitätsbudget", C.BUDGET_CHOICES, key="budget_radio", horizontal=True,
                      help="Frei: so viel Kapazität wie gewünscht. Knapp: höchstens 95 % der mittleren Gesamtnachfrage, das Budget bindet immer.")
    transfer = st.radio("Umlagerung zwischen Standorten", C.TRANSFER_CHOICES, key="transfer_radio", horizontal=True,
                        help="An: ungenutzte Kapazität eines Standorts kann den Bedarf eines anderen decken (mit Transportkosten).")
    st.markdown("**Instanz**")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({
    "s_slider": int(s), "sigma_slider": sigma, "lam_slider": lam, "alpha_radio": alpha, "budget_radio": budget,
    "transfer_radio": transfer, "seed_input": int(seed), "draw_input": int(draw),
})

settings = Settings(s=int(s), sigma=float(sigma), lam=float(lam), alpha=float(alpha), budget=str(budget),
                    transfer=str(transfer), seed=int(seed), draw=int(draw))
exp_key = Settings(s=C.DEFAULT_S, sigma=settings.sigma, lam=settings.lam, alpha=settings.alpha, budget=settings.budget,
                   transfer=settings.transfer, seed=settings.seed, draw=settings.draw)

# --- Ergebnis ----------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Mittelwertplan gegen Risikoplan")
if settings.lam == 0.0:
    st.info("Bei λ = 0 sind Mittelwert- und Risikoplan derselbe Plan. Stellen Sie λ höher, um den Tausch zu sehen.")
with st.spinner("Löse die Planungsprobleme und werte sie auf 600 Referenzszenarien aus …"):
    a = _analysis(settings)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Mittel der Kosten, Risikoplan", f"{a.risk_plan.mean:,.0f}".replace(",", "."), delta=f"{_pct(a.mean_change_pct)} gegen Mittelwertplan", delta_color="inverse")
m2.metric(f"CVaR {round((1 - settings.alpha) * 100)} %, Risikoplan", f"{a.risk_plan.cvar:,.0f}".replace(",", "."), delta=f"{_pct(a.cvar_change_pct)} gegen Mittelwertplan", delta_color="inverse")
m3.metric("Mittel, Mittelwertplan", f"{a.mean_plan.mean:,.0f}".replace(",", "."), delta="Referenz", delta_color="off")
m4.metric(f"CVaR {round((1 - settings.alpha) * 100)} %, Mittelwertplan", f"{a.mean_plan.cvar:,.0f}".replace(",", "."), delta="Referenz", delta_color="off")
st.plotly_chart(build_distribution(a.mean_plan, a.risk_plan, settings.alpha), width="stretch", key="distribution_chart")
st.caption("Verteilung der Gesamtkosten über die 600 Referenzszenarien. Der Risikoplan verschiebt Kosten aus dem rechten Tail in die Mitte, bezahlt dafür aber im Mittel.")

left, right = st.columns(2)
with left:
    st.plotly_chart(build_frontier(a.frontier, settings.lam), width="stretch", key="frontier_chart")
    st.caption("Kurve aus derselben Stichprobe: Erwartungswert gegen CVaR je Gewicht λ, auf der Referenz ausgewertet.")
with right:
    st.plotly_chart(build_plans(build_instance(settings).mu, a.x_mean, a.x_risk), width="stretch", key="plans_chart")
    st.caption("Der Risikoplan hält an den meisten Standorten mehr Kapazität vor: Er kauft Sicherheit ein.")

# --- Kernfrage ---------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Lohnt es sich, den Tail zu drücken?")
tail_n = max(1, round((1 - settings.alpha) * settings.s))
if a.verdict == "kein_unterschied":
    if settings.lam == 0.0:
        st.info("Mit λ = 0 gibt es keinen Risikoplan.")
    else:
        st.info(
            f"**Hier ändert das Risikomaß kaum etwas:** Der Risikoplan verändert den CVaR um {_pct(a.cvar_change_pct)} und die mittleren Kosten um {_pct(a.mean_change_pct)}. "
            "Bei knappem Kapazitätsbudget wird nur verteilt, nicht zusätzlich vorgehalten: Es gibt keinen Spielraum, den Tail zu drücken."
        )
elif a.verdict == "tausch":
    price = a.mean_change_pct
    gain = -a.cvar_change_pct
    st.success(
        f"**Ein Tausch:** Der Tail sinkt um {_de(gain)} %, dafür steigen die mittleren Kosten um {_de(price)} %. "
        f"Je gewonnenem Prozent Tail kostet das {_de(price / gain, 2)} Prozent im Mittel."
    )
else:
    st.warning(f"**Nur Kosten, kein Gewinn:** mittlere Kosten {_pct(a.mean_change_pct)}, CVaR {_pct(a.cvar_change_pct)}.")
st.caption(
    f"Der Tail besteht in der Stichprobe aus {tail_n} Szenarien ((1 − α) · S). Mit wenigen Szenarien ist der Risikoplan unsicher: "
    "Er kann auf der Referenz schlechter abschneiden als ein Plan mit weniger Gewicht auf dem Tail (siehe Pareto-Kurve und Experiment)."
)

st.markdown("---")

# --- Experiment --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Braucht der Risikoplan mehr Szenarien?")
st.caption(
    f"Je Szenarienzahl ({', '.join(str(v) for v in C.SWEEP_S)}) {C.DRAWS} Ziehungen. Regret = Mehrkosten des Stichprobenplans gegenüber dem besten Plan auf der "
    "Referenz, jeweils im eigenen Ziel (Mittelwertplan im Mittel, Risikoplan im gemischten Ziel). Die Szenarienzahl-Regler wirkt hier nicht; λ, α, Streuung, Budget, Umlagerung und Ziehung gelten."
)
if st.button("Experiment starten (ca. 30 Sekunden)", key="run_experiment"):
    st.session_state["experiment_done"] = exp_key
if st.session_state.get("experiment_done") == exp_key:
    with st.spinner(f"Rechne {len(C.SWEEP_S) * C.DRAWS} Ziehungen …"):
        rows = _experiment(exp_key)
    st.plotly_chart(build_experiment(rows), width="stretch", key="experiment_chart")
    table = [
        {"S": r["s"], "Regret Mittelwertplan (%)": round(r["regret_mean"], 2), "Regret Risikoplan (%)": round(r["regret_risk"], 2),
         "Risikoplan 90. Perz. (%)": round(r["regret_risk_p90"], 2), "Plan weicht ab, Mittelwertplan (%)": round(r["dev_mean"], 1),
         "Plan weicht ab, Risikoplan (%)": round(r["dev_risk"], 1)}
        for r in rows
    ]
    st.dataframe(table, hide_index=True, width="stretch")
    first = rows[0]
    if exp_key.lam > 0 and first["regret_mean"] > 0:
        st.info(
            f"Bei {first['s']} Szenarien liegt der Regret des Risikoplans im Mittel bei {_de(first['regret_risk'], 2)} % gegenüber "
            f"{_de(first['regret_mean'], 2)} % beim Mittelwertplan, das {_de(first['regret_risk'] / first['regret_mean'], 1)}-Fache. Der Tail ist die "
            "dünnste Stelle der Stichprobe."
        )
else:
    st.info("Das Experiment läuft auf Knopfdruck, weil es mehr als hundert Optimierungen rechnet.")

st.markdown("---")

# --- Grenzen -----------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Kapazität ist frei wählbar** | Bei knappem Budget wird nur verteilt: Der Risikoplan unterscheidet sich kaum vom Mittelwertplan, es gibt nichts Zusätzliches zu kaufen. | – |
| **CVaR ist das richtige Risikomaß** | Es ist eines unter mehreren (Varianz, Wahrscheinlichkeit einer Überschreitung, Worst Case). Es erfasst den Tail im Mittel, nicht dessen Form. | – |
| **Die Stichprobe zeigt den Tail** | Der Tail besteht nur aus (1 − α) · S Szenarien. Seltene Ereignisse, die in der Stichprobe fehlen, kennt der Plan nicht. | [Stichproben-Demo (SAA)](https://github.com/sebastian-hanisch/saa-demo): wie viele Szenarien der Erwartungswertplan braucht |
| **Die 600 Referenzszenarien sind die wahre Verteilung** | Das ist eine Setzung; eine echte Verteilung hat mehr Rand, und der echte CVaR liegt vermutlich höher. | – |
| **Ein Vehikel, feste Preise** | Wie viel der Risikoplan kostet, hängt an Streuung, Zukaufpreis und Fehlmenge-Strafe; die Zahlen lassen sich nicht auf andere Probleme übertragen. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** Wie in der Wurzel der Linie: Stufe 1 Kapazität $x\ge 0$ mit Kosten $c\,\mathbf 1^\top x$ und Budget; Stufe 2 Kosten $Q(x,\xi)$ (Umlagerung, Zukauf, Fehlmenge).
Die Gesamtkosten eines Szenarios sind $T_s(x)=c\,\mathbf 1^\top x+Q(x,\xi_s)$.

**CVaR.** Für das Niveau $\alpha$ ist $\mathrm{CVaR}_\alpha(T)=\min_{\eta}\Big\{\eta+\tfrac1{1-\alpha}\,\mathbb E\big[(T-\eta)^+\big]\Big\}$, bei $S$ gleich wahrscheinlichen Szenarien das Mittel der
teuersten $(1-\alpha)S$ Werte (ein nicht ganzzahliger Rand zählt anteilig). Mit Überschreitungen $z_s\ge 0$ wird daraus ein LP:
$$\min_{x,\eta,z,\,\text{Stufe 2}}\;\; c\,\mathbf 1^\top x+(1-\lambda)\tfrac1S\sum_s Q_s+\lambda\Big(\eta+\tfrac1{(1-\alpha)S}\sum_s z_s\Big)\quad\text{u. d. N.}\quad z_s\ge Q_s-\eta,\;\;z_s\ge 0.$$
Der erste Term $c\,\mathbf 1^\top x$ ist deterministisch und verschiebt den CVaR genau um sich selbst, deshalb genügt es, den CVaR der Stufe-2-Kosten zu bilden.

**Eigenschaften.** $\mathrm{CVaR}_\alpha$ ist kohärent und konvex in $x$; bei $\lambda=0$ ist der Plan der Mittelwertplan, bei $\lambda=1$ der reine CVaR-Plan. Pläne für $\lambda\in(0,1)$ liegen
auf der Pareto-Kurve aus Erwartungswert und CVaR; wie viele Szenarien man für einen stabilen Plan braucht, steigt, weil nur $(1-\alpha)S$ Szenarien den Tail bestimmen.

**Literatur.** Rockafellar & Uryasev, *Optimization of Conditional Value-at-Risk*, Journal of Risk 2(3), 2000, S. 21–41 (Theoreme 1 und 2: LP-Darstellung für Szenarien);
dort heißen das Niveau β und die Hilfsvariable α, die Formel oben ist dieselbe in der in der Stochastik üblichen Notation.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
