
"""
Rule-based anomaly detection over thruster telemetry.

Mirrors how ops teams flag off-nominal behavior: simple thresholds
and rate-of-change checks, not ML -- fast, explainable, and auditable,
which is what you want when a human has to act on the alert.
"""

import pandas as pd
import numpy as np


def detect_anomalies(df: pd.DataFrame,
                      current_nom_A: float, thrust_nom_N: float,
                      current_threshold_pct: float = 0.4,
                      temp_rate_threshold_C_per_hr: float = 5.0,
                      thrust_dropout_frac: float = 0.2) -> pd.DataFrame:
    """
    Applies three independent rule-based checks and flags each sample.
    Returns df with added boolean columns per rule + a combined flag.
    """
    df = df.copy()

    # Rule 1: overcurrent -- current exceeds nominal by more than threshold pct
    df["flag_overcurrent"] = df["current_A"] > current_nom_A * (1 + current_threshold_pct)

    # Rule 2: thermal runaway -- rate of change of temp exceeds threshold
    lookback_samples = 30  # 30 min lookback at 60s sampling — averages out noise
    temp_smooth = df["temp_C"].rolling(window=10, center=True, min_periods=1).mean()
    dtemp = temp_smooth.diff(periods=lookback_samples)
    dt_hr = df["t_s"].diff(periods=lookback_samples) / 3600
    rate_C_per_hr = np.where(dt_hr > 0, dtemp / dt_hr, 0)
    df["temp_rate_C_per_hr"] = rate_C_per_hr
    df["temp_rate_C_per_hr"] = rate_C_per_hr
    df["flag_thermal"] = df["temp_rate_C_per_hr"] > temp_rate_threshold_C_per_hr

    # Rule 3: thrust dropout -- thrust drops well below nominal while it should be firing
    df["flag_dropout"] = df["thrust_N"] < thrust_nom_N * thrust_dropout_frac

    df["flag_any"] = df["flag_overcurrent"] | df["flag_thermal"] | df["flag_dropout"]
    return df


def summarize_events(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse consecutive flagged samples into discrete events for a report."""
    events = []
    in_event = False
    start_idx = None
    for i, flagged in enumerate(df["flag_any"]):
        if flagged and not in_event:
            in_event = True
            start_idx = i
        elif not flagged and in_event:
            in_event = False
            events.append((start_idx, i - 1))
    if in_event:
        events.append((start_idx, len(df) - 1))

    rows = []
    for s, e in events:
        chunk = df.iloc[s:e + 1]
        cause = []
        if chunk["flag_overcurrent"].any():
            cause.append("overcurrent")
        if chunk["flag_thermal"].any():
            cause.append("thermal_runaway")
        if chunk["flag_dropout"].any():
            cause.append("thrust_dropout")
        rows.append({
            "start_t_hr": round(df["t_s"].iloc[s] / 3600, 2),
            "end_t_hr": round(df["t_s"].iloc[e] / 3600, 2),
            "duration_min": round((df["t_s"].iloc[e] - df["t_s"].iloc[s]) / 60, 1),
            "likely_cause": ", ".join(cause),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = pd.read_csv("telemetry/telemetry_log.csv")

    result = detect_anomalies(df, current_nom_A=1.8, thrust_nom_N=0.040)
    events = summarize_events(result)

    print("=== Anomaly Report ===")
    print(events.to_string(index=False) if not events.empty else "No anomalies detected.")

    # Validate against injected ground truth
    detected_samples = result["flag_any"].sum()
    injected_samples = result["injected_anomaly"].sum()
    true_positives = (result["flag_any"] & result["injected_anomaly"]).sum()

    print(f"\nInjected anomaly samples: {injected_samples}")
    print(f"Detected anomaly samples: {detected_samples}")
    print(f"True positive samples:    {true_positives}")
    if injected_samples > 0:
        print(f"Recall: {true_positives / injected_samples:.1%}")

    result.to_csv("anomaly/anomaly_log.csv", index=False)