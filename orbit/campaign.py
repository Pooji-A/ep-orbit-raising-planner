"""
Burn-arc, eclipse-aware orbit-raising campaign planner.
 
Upgrade over the plain Edelbaum duration estimate: EP thrusters are
power-limited, so they only fire during sunlit arcs and coast through
eclipse. This simulates the maneuver day-by-day, the way a propulsion
ops team would actually track progress against a plan -- burn time
today, delta-v achieved, delta-v remaining, replanned each day.
"""
 
import numpy as np
import pandas as pd
from Edelbaum import edelbaum_delta_v, MU_EARTH, R_EARTH
 
 
def orbital_period_s(radius_km: float) -> float:
    return 2 * np.pi * np.sqrt(radius_km**3 / MU_EARTH)
 
 
def eclipse_fraction(beta_deg: float) -> float:
    """
    Simplified eclipse fraction of orbit period as a function of beta
    angle (angle between orbital plane and the sun vector).
    beta ~90 deg (dawn-dusk SSO) -> ~0 eclipse (continuous sun).
    beta ~0 deg -> worst case, ~35% of the orbit in shadow.
    This is a geometric approximation, not a full illumination model.
    """
    max_eclipse_frac = 0.35
    beta_rad = np.radians(beta_deg)
    return max_eclipse_frac * max(0.0, np.cos(beta_rad))
 
 
def simulate_campaign(alt_start_km: float, alt_target_km: float, incl_deg: float,
                       mass_kg: float, thrust_N: float, isp_s: float,
                       beta_deg: float = 60.0, max_days: int = 30) -> tuple[pd.DataFrame, float]:
    """
    Day-by-day burn-arc campaign simulation.
 
    Each day: compute sunlit fraction, accumulate burn time only during
    sunlit arcs, apply that thrust to reduce remaining delta-v, and log
    the daily state -- mirroring a real ops maneuver-tracking cycle.
    """
    dv_total_ms = edelbaum_delta_v(alt_start_km, alt_target_km, incl_deg, incl_deg) * 1000
    accel = thrust_N / mass_kg  # m/s^2, ~constant mass assumption (small prop fraction)
 
    dv_achieved_ms = 0.0
    alt_now = alt_start_km
    log = []
    day = 0
 
    while dv_achieved_ms < dv_total_ms and day < max_days:
        day += 1
        radius_km = R_EARTH + alt_now
        period_s = orbital_period_s(radius_km)
        sunlit_frac = 1 - eclipse_fraction(beta_deg)
 
        burn_time_s_today = 86400 * sunlit_frac  # total sunlit seconds today
        dv_today_ms = min(accel * burn_time_s_today, dv_total_ms - dv_achieved_ms)
        dv_achieved_ms += dv_today_ms
 
        frac_complete = dv_achieved_ms / dv_total_ms
        alt_now = alt_start_km + frac_complete * (alt_target_km - alt_start_km)
 
        log.append({
            "day": day,
            "sunlit_fraction": round(sunlit_frac, 3),
            "burn_time_hr": round(burn_time_s_today / 3600, 2),
            "dv_today_ms": round(dv_today_ms, 3),
            "dv_achieved_ms": round(dv_achieved_ms, 3),
            "dv_remaining_ms": round(dv_total_ms - dv_achieved_ms, 3),
            "alt_estimate_km": round(alt_now, 2),
        })
 
    return pd.DataFrame(log), dv_total_ms
 
 
if __name__ == "__main__":
    df, dv_total = simulate_campaign(
        alt_start_km=450.0, alt_target_km=570.0, incl_deg=97.6,
        mass_kg=130.0, thrust_N=0.040, isp_s=1500.0,
        beta_deg=60.0,  # not a pure dawn-dusk orbit -> some eclipse each day
    )
    print(f"Total delta-v required: {dv_total:.2f} m/s\n")
    print(df.to_string(index=False))
    print(f"\nCampaign complete in {len(df)} day(s) of burn-arc operations "
          f"(vs a naive continuous-thrust estimate that ignores eclipse).")
 
