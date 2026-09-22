
"""
Ground-pass telemetry gating.

Real ops doesn't get continuous telemetry -- data only comes down
during ground-station contacts. This takes the full "truth" telemetry
log and produces a "downlinked" version that's only visible during
simulated pass windows, plus flags anomalies that occurred during a
blackout (i.e. weren't seen until the next pass).
"""

import numpy as np
import pandas as pd


def generate_pass_schedule(duration_days: float, passes_per_day: int = 2,
                            pass_duration_min: float = 10.0, seed: int = 7) -> list[tuple[float, float]]:
    """
    Returns a list of (start_s, end_s) ground-pass windows spread
    roughly evenly across the campaign, with small random jitter to
    mimic real orbit-to-groundstation geometry.
    """
    rng = np.random.default_rng(seed)
    total_s = duration_days * 86400
    n_passes = int(duration_days * passes_per_day)
    spacing = total_s / n_passes

    windows = []
    for i in range(n_passes):
        jitter = rng.uniform(-spacing * 0.15, spacing * 0.15)
        start = i * spacing + spacing / 2 + jitter
        start = max(0, start)
        end = start + pass_duration_min * 60
        windows.append((start, end))
    return windows


def gate_telemetry(df: pd.DataFrame, pass_windows: list[tuple[float, float]]) -> pd.DataFrame:
    """
    Returns only the telemetry samples that fall within a pass window
    -- i.e. what ops would actually have "on the ground" to look at.
    """
    mask = np.zeros(len(df), dtype=bool)
    for start, end in pass_windows:
        mask |= (df["t_s"] >= start) & (df["t_s"] <= end)
    return df[mask].reset_index(drop=True)


def find_blackout_anomalies(df: pd.DataFrame, pass_windows: list[tuple[float, float]]) -> pd.DataFrame:
    """
    Identifies injected anomalies that occurred *outside* any pass
    window -- these wouldn't be seen in real time, only discovered
    (possibly late) at the next contact.
    """
    in_pass = np.zeros(len(df), dtype=bool)
    for start, end in pass_windows:
        in_pass |= (df["t_s"] >= start) & (df["t_s"] <= end)

    blackout_anomalies = df[df["injected_anomaly"] & ~in_pass]
    return blackout_anomalies


if __name__ == "__main__":
    df = pd.read_csv("telemetry/telemetry_log.csv")
    duration_days = df["t_s"].max() / 86400

    passes = generate_pass_schedule(duration_days, passes_per_day=2, pass_duration_min=10.0)
    print(f"Generated {len(passes)} ground-pass windows over {duration_days:.1f} days\n")

    downlinked = gate_telemetry(df, passes)
    blackout = find_blackout_anomalies(df, passes)

    print(f"Full (onboard) samples:     {len(df)}")
    print(f"Downlinked samples:         {len(downlinked)} ({len(downlinked)/len(df):.1%} of total)")
    print(f"Anomalous samples in truth: {df['injected_anomaly'].sum()}")
    print(f"Anomalous samples seen live: {downlinked['injected_anomaly'].sum()}")
    print(f"Anomalies missed until next pass (blackout): {len(blackout)} samples")

    if not blackout.empty:
        first_missed_hr = blackout["t_s"].min() / 3600
        # find next pass after this
        next_pass = min((s for s, e in passes if s / 3600 > first_missed_hr), default=None)
        if next_pass:
            delay_hr = next_pass / 3600 - first_missed_hr
            print(f"\nExample: anomaly at t={first_missed_hr:.2f}h occurred during a blackout; "
                  f"not visible until next pass at t={next_pass/3600:.2f}h "
                  f"(~{delay_hr:.2f}h detection delay).")

    downlinked.to_csv("telemetry/downlinked_log.csv", index=False)