
# EP Orbit-Raising Planner

A small end-to-end simulation of an electric-propulsion orbit-raising
campaign for a smallsat, built to demonstrate the core technical areas
of a propulsion operations role: orbital dynamics, electric propulsion
sizing, anomaly response, and ops procedure design.

## What it does

1. **`orbit/edelbaum.py`** — Sizes the maneuver: delta-v, propellant
   mass, and a naive continuous-thrust duration estimate, using
   Edelbaum's closed-form approximation for low-thrust circular-to-
   circular transfers.

2. **`orbit/campaign.py`** — Upgrades the estimate to something closer
   to real ops: EP thrusters are power-limited, so they only fire
   during sunlit arcs and coast through eclipse. Simulates the
   maneuver day-by-day, replanning remaining delta-v against progress,
   the way a propulsion ops team actually tracks a campaign.

3. **`telemetry/simulate.py`** — Generates synthetic thruster telemetry
   (thrust, bus current, temperature) over the campaign, with three
   injected anomalies: an overcurrent event, a thermal runaway trend,
   and a thrust dropout.

4. **`telemetry/ground_pass_gate.py`** — Filters the full telemetry down
   to only what would be visible during simulated ground-station passes,
   and flags anomalies that occurred during a blackout window.

5. **`anomaly/detect.py`** — Rule-based anomaly detection over the
   telemetry (threshold + rate-of-change checks), validated against
   the injected ground truth, with a collapsed event report.

6. **`docs/ops_runbook.md`** — The maneuver plan summary and a response
   procedure for each anomaly type, plus a pre-campaign verification
   checklist.

## Why this shape

Real propulsion ops work isn't a single calculation — it's sizing a
maneuver, planning its execution against real constraints (power,
eclipse, ground contact), watching telemetry for off-nominal behavior,
and having a defined response when something goes wrong. This project
is a small, self-contained version of that loop.

## Run it

```bash
python orbit/edelbaum.py
python orbit/campaign.py
python telemetry/simulate.py
python telemetry/ground_pass_gate.py
python anomaly/detect.py
```

## Possible extensions

- Replace the closed-form Edelbaum sizing with numerical propagation
  (e.g. via GMAT or a custom integrator) for a higher-fidelity plan
- Machine-learning-based anomaly detection as a comparison baseline
  against the rule-based approach
  