"""
Synthetic thruster telemetry generator.

Simulates thrust, bus current, and thruster temperature over the
orbit-raising transfer, with a couple of injected anomalies to be
caught by the anomaly-detection stage.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "orbit"))
from Edelbaum import edelbaum_delta_v, transfer_duration


def simulate_telemetry(thrust_nom_N: float, current_nom_A: float,
                        temp_nom_C: float, duration_days: float,
                        sample_interval_s: int = 60, seed: int = 42) -> pd.DataFrame:
    """
    Generate a synthetic telemetry time series for a continuous-thrust
    orbit-raising maneuver, with injected anomalies.
    """
    rng = np.random.default_rng(seed)

    n_samples = int(duration_days * 86400 / sample_interval_s)
    t = np.arange(n_samples) * sample_interval_s  # seconds since start

    # Nominal signals + realistic noise
    thrust = thrust_nom_N + rng.normal(0, thrust_nom_N * 0.02, n_samples)
    current = current_nom_A + rng.normal(0, current_nom_A * 0.03, n_samples)
    temp = temp_nom_C + rng.normal(0, 0.5, n_samples)

    # slow nominal thermal ramp as thruster warms up over the burn
    temp += np.linspace(0, 8, n_samples)

    # --- Inject anomalies ---
    anomaly_flags = np.zeros(n_samples, dtype=bool)

    # 1) Current spike (~overcurrent event), short duration
    spike_start = int(n_samples * 0.35)
    spike_len = max(1, int(300 / sample_interval_s))  # ~5 min
    current[spike_start:spike_start + spike_len] += current_nom_A * 0.9
    anomaly_flags[spike_start:spike_start + spike_len] = True

    # 2) Thermal runaway trend over ~1 hour
    runaway_start = int(n_samples * 0.6)
    runaway_len = max(1, int(3600 / sample_interval_s))
    runaway_end = min(n_samples, runaway_start + runaway_len)
    temp[runaway_start:runaway_end] += np.linspace(0, 25, runaway_end - runaway_start)
    anomaly_flags[runaway_start:runaway_end] = True

    # 3) Thrust dropout (thruster safed / momentary fault)
    dropout_start = int(n_samples * 0.8)
    dropout_len = max(1, int(600 / sample_interval_s))  # 10 min
    thrust[dropout_start:dropout_start + dropout_len] = 0.0
    anomaly_flags[dropout_start:dropout_start + dropout_len] = True

    df = pd.DataFrame({
        "t_s": t,
        "thrust_N": thrust,
        "current_A": current,
        "temp_C": temp,
        "injected_anomaly": anomaly_flags,  # ground truth, for validating detector
    })
    return df


if __name__ == "__main__":
    # Use the same scenario as the orbit-raising calculator
    thrust_N = 0.040
    isp_s = 1500.0
    mass_kg = 130.0

    dv = edelbaum_delta_v(450.0, 570.0, 97.6, 97.6)
    duration_days = transfer_duration(dv, thrust_N, mass_kg)

    df = simulate_telemetry(
        thrust_nom_N=thrust_N,
        current_nom_A=1.8,     # typical bus current draw for a small EP thruster
        temp_nom_C=45.0,       # nominal operating temp, deg C
        duration_days=duration_days,
    )

    df.to_csv("telemetry/telemetry_log.csv", index=False)
    print(f"Generated {len(df)} samples over {duration_days:.1f} days")
    print(df.describe())

    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    axes[0].plot(df["t_s"] / 3600, df["thrust_N"])
    axes[0].set_ylabel("Thrust (N)")
    axes[1].plot(df["t_s"] / 3600, df["current_A"])
    axes[1].set_ylabel("Current (A)")
    axes[2].plot(df["t_s"] / 3600, df["temp_C"])
    axes[2].set_ylabel("Temp (C)")
    axes[2].set_xlabel("Time (hours)")
    plt.tight_layout()
    plt.savefig("telemetry/telemetry_plot.png")
    print("Saved plot to telemetry/telemetry_plot.png")