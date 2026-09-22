"""
Electric Propulsion Orbit-Raising Planning
Iam using Edelbaum's approximation for low-thrust, circular-to circular orbit transfers with ana optional inclination change.
"""

#Required Libraries 

import numpy as np

#Defining constants

MU_EARTH = 398600.4418  #Km^3/S^2
R_EARTH = 6378.137      #Km
G0 = 9.80665            #M/S^2


def circular_velocity(radius_km: float) -> float:
    """Circular orbital velocity (km/s) at a given radius."""
    return np.sqrt(MU_EARTH / radius_km)
 
 
def edelbaum_delta_v(alt1_km: float, alt2_km: float,
                      incl1_deg: float = 0.0, incl2_deg: float = 0.0) -> float:
    """
    Delta-v (km/s) for a low-thrust circular-to-circular transfer
    with a plane change, using Edelbaum's closed-form approximation.
 
    alt1_km, alt2_km : initial/target altitude above Earth's surface (km)
    incl1_deg, incl2_deg : initial/target inclination (deg)
    """
    r1 = R_EARTH + alt1_km
    r2 = R_EARTH + alt2_km
 
    v1 = circular_velocity(r1)
    v2 = circular_velocity(r2)
 
    delta_i_rad = np.radians(abs(incl2_deg - incl1_deg))
 
    # Edelbaum's equation
    dv = np.sqrt(v1**2 + v2**2 - 2 * v1 * v2 * np.cos(delta_i_rad * np.pi / 2))
 
    return dv
 
 
def propellant_mass(delta_v_km_s: float, m0_kg: float, isp_s: float) -> float:
    """Tsiolkovsky rocket equation -> propellant mass (kg)."""
    dv_m_s = delta_v_km_s * 1000
    mf = m0_kg * np.exp(-dv_m_s / (isp_s * G0))
    return m0_kg - mf
 
 
def transfer_duration(delta_v_km_s: float, thrust_N: float, m0_kg: float) -> float:
    """
    Rough transfer duration (days) assuming continuous thrust and
    roughly constant mass (valid for small propellant fraction, typical
    of small-sat EP orbit raising).
    """
    dv_m_s = delta_v_km_s * 1000
    accel = thrust_N / m0_kg  # m/s^2
    seconds = dv_m_s / accel
    return seconds / 86400.0  # -> days
 
 
if __name__ == "__main__":
    # Example: SSO smallsat, ~500 km target, small EP thruster
    alt_start = 450.0   # km, injection altitude
    alt_target = 570.0  # km, operational altitude
    incl = 97.6          # deg, sun-synchronous, no plane change needed
 
    mass = 130.0         # kg, spacecraft wet mass
    thrust = 0.040        # N, e.g. small Hall-effect / gridded ion thruster
    isp = 1500.0          # s
 
    dv = edelbaum_delta_v(alt_start, alt_target, incl, incl)
    m_prop = propellant_mass(dv, mass, isp)
    days = transfer_duration(dv, thrust, mass)
 
    print(f"Delta-v required:      {dv*1000:.2f} m/s")
    print(f"Propellant mass:       {m_prop:.3f} kg")
    print(f"Estimated duration:    {days:.1f} days")
