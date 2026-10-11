# Risiko als Ziel: Erwartungswert und CVaR – Streamlit-Demo

Drittes Stück der **Optimierung-unter-Unsicherheit-Linie** der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“.
Anders als die Fall-Demos (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt sie **ein** Verfahren, die Optimierung auf den **CVaR**, an einem wachsenden Beispiel.
**Kante in der Linie:** Sie behebt eine Annahme der Wurzel [newsvendor-evpi-demo](https://github.com/sebastian-hanisch/newsvendor-evpi-demo) und der Stichproben-Demo
[saa-demo](https://github.com/sebastian-hanisch/saa-demo): Beide optimieren den Erwartungswert. Hier ist das Ziel der **Tail**: die Kosten der teuersten Szenarien.
Das Vehikel ist dasselbe: Kapazitätsvorhaltung mit Zukauf, Umlagerung und Fehlmenge, sechs Standorte, als lineares Programm.

## Warum dieses Problem

Ein Plan, der im Mittel am billigsten ist, kann in den schlechtesten Szenarien sehr teuer werden. Wer den Tail drücken will, zahlt dafür im Mittel. Die Demo misst **wie viel**, und
zeigt, wann es sich nicht lohnt (knappes Budget) und wie viele Szenarien man für einen stabilen Risikoplan braucht.

## Modell

Dasselbe Modell wie in der Wurzel (Stufe 1 Kapazität zu 1 je Einheit, Stufe 2 Umlagerung, Zukauf bis 50 % der Nachfrage, Fehlmenge dreifach bestraft). Das Kapazitätsbudget ist **frei** oder **knapp**
(höchstens 95 % der mittleren Gesamtnachfrage). **Die Verteilung** besteht aus 600 gleich wahrscheinlichen Szenarien; eine **Stichprobe** sind S Ziehungen mit Zurücklegen daraus.
Ziel des Risikoplans: (1 − λ) · Mittel + λ · CVaR_α der Gesamtkosten, α ∈ {80, 90, 95 %}. Formeln im 📐-Expander der App.

## Methodik

- **Mittelwertplan:** minimiert das Mittel der Kosten auf der Stichprobe (λ = 0).
- **Risikoplan:** minimiert (1 − λ) · Mittel + λ · CVaR (Rockafellar und Uryasev, ein LP mit Hilfsvariable η und Überschreitungen z_s).
- **Prüfen:** beide Pläne auf den 600 Referenzszenarien ausgewertet; Mittel, CVaR und die ganze Kostenverteilung.
- **Pareto-Kurve:** λ ∈ {0; 0,25; 0,5; 0,75; 1} aus derselben Stichprobe.
- **Experiment:** je Szenarienzahl (20, 50, 100, 200) 16 Ziehungen; Regret beider Pläne im eigenen Ziel gegen den Referenzplan.

## Befunde (gemessen, keine Behauptungen)

Voreinstellung (Seed 7, Ziehung 1, S = 100, α = 90 %, Streuung 35 %, Kapazität frei, Umlagerung an); jede Aussage in `tests/test_claims.py` als Band belegt.

| Frage | Befund |
|---|---|
| **Was kostet der Tail?** | λ = 0,5: Mittel +18,5 %, CVaR −21,0 %. λ = 1: Mittel +31,0 %, CVaR −20,9 %. Über fünf Ziehungen (Median) kostet λ = 0,25 im Mittel +2,6 % bei −7,9 % CVaR; λ = 1 +26 % bei −21 %. |
| **Wird der Tausch teurer?** | Ja: je gewonnenem Prozent Tail kostet es im Mittel 0,33 (λ = 0,25), 0,88 (0,5), 1,30 (0,75) und 1,36 (1) Prozent. Die letzten Schritte gewinnen kaum noch Tail. |
| **Überpasst der reine CVaR-Plan?** | In dieser Ziehung hat λ = 0,75 auf der Referenz einen niedrigeren CVaR (924) als λ = 1 (931): Der Tail besteht bei α = 90 % aus nur 10 Szenarien. |
| **Wie hängt es am Tail α?** | λ = 1: Mittel +17 % bei α = 80 %, +31 % bei 90 %, +43 % bei 95 %. Je tiefer der Tail, desto teurer. |
| **Wann ändert es kaum etwas?** | Bei knappem Budget (bindet immer): Mittel +0,14 %, CVaR −1,0 %. Es wird nur verteilt. |
| **Braucht der Risikoplan mehr Szenarien?** | Ja, etwa die zehnfache Zahl: Regret des Risikoplans bei 200 Szenarien 0,55 % gegenüber 0,64 % des Mittelwertplans bei 20. Bei 20 Szenarien 3,6 % gegenüber 0,64 %; das Planverhalten schwankt 20 % gegen 9 %. |

## Ehrliche Grenzen

- **Die Referenz ist gesetzt, nicht gefunden.** Die 600 Szenarien sind die Verteilung; eine echte Verteilung hat mehr Rand, und der echte Tail liegt vermutlich höher.
- **Nur CVaR.** Es ist ein Risikomaß unter mehreren und erfasst den Tail im Mittel, nicht dessen Form.
- **Eine Instanz, wenige Ziehungen.** Die Pareto-Kurve stammt aus einer Ziehung; die Median-Werte über fünf Ziehungen und das Experiment (16 Ziehungen je Szenarienzahl) tragen Stichprobenfehler. Ordnung und Größenordnung sind belastbar.
- **Das Bild hängt an der freien Kapazität.** Bei knappem Budget gibt es kaum etwas zu gewinnen.

## Verifikation

- **Kern:** CVaR an Handbeispielen (auch mit Bruchteil am Rand), Stufe-2-Kosten an der Mini-Instanz, λ = 0 gleich dem Mittelwert-LP, Zielwert gleich (1 − λ) Mittel + λ CVaR der ausgewerteten Kosten, Budget bindet bei „knapp“.
- **Orakel (`tests/test_oracle_cvar.py`):** dasselbe Risiko-LP als eigenes Modell in OR-Tools (GLOP) mit und ohne Umlagerung (1e-7); der CVaR gegen die Minimierungs-Definition über η; kein Zufallsplan schlägt das LP-Optimum.
- **Claims (`tests/test_claims.py`):** Tausch, Reihenfolge der Pareto-Kurve, knappes Budget, Tiefe des Tails, Szenarienbedarf.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), Experiment-Knopf, Footer.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App |
| `cvr_rng.py` | SplitMix64, Standardnormale per Inversion |
| `cvr_scenario.py` | Instanz und Nachfrage-Szenarien (wie in der Wurzel) |
| `cvr_algorithm.py` | Stufe-2-Block und ein LP je Informationsstruktur (wie in der Wurzel) |
| `cvr_cvar.py` | CVaR, Risiko-LP, Auswertung eines Plans |
| `cvr_evaluation.py` | Analyse, Pareto-Kurve, Experiment, Verdikt |
| `cvr_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `cvr_presets.py` | Permalink (Begrenzen, Einrasten), Presets, Zufalls-Seed-Buttons |
| `cvr_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tools/measure_stueck3.py` | Messreihe für README und Claims |
| `tests/` | Mini-Instanz, Orakel, Claims, Presets, AppTest-Smoke-Test, Footer |

## Bewusst nicht umgesetzt

- **Andere Risikomaße** (Varianz, Wahrscheinlichkeit einer Überschreitung): eigene Frage mit anderer Antwort.
- **Chance-Constraints und robuste Mengen:** garantieren statt gewichten, ein anderes Konzept.
- **Verteilungsshift:** Der Tail kommt aus derselben Verteilung wie die Stichprobe.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Unsicherheit: von EVPI bis rollierend](https://sebastianhanisch.net/konzepte-optimierung-unsicherheit.html).
