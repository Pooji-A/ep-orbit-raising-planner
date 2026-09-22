
# Propulsion Ops Runbook — EP Orbit-Raising Campaign

## Maneuver Summary

| Parameter | Value |
|---|---|
| Start altitude | 450 km |
| Target altitude | 570 km |
| Inclination | 97.6° (sun-synchronous) |
| Spacecraft mass | 130 kg |
| Thruster | 40 mN, Isp 1500 s |
| Total delta-v | ~66.3 m/s |
| Propellant budget | ~0.58 kg |
| Campaign duration | 4 days (eclipse-aware, beta = 60°) |

Delta-v sized via Edelbaum's approximation (`orbit/edelbaum.py`); execution
plan generated day-by-day accounting for eclipse-limited burn arcs
(`orbit/campaign.py`).

## Daily Operating Procedure

1. Confirm spacecraft health (bus voltage, thermal state) before enabling
   thruster for the day's burn window.
2. Enable thrust for the sunlit arc; monitor thrust, current, and
   temperature telemetry during the pass.
3. At end of burn window, compare achieved delta-v against plan
   (`campaign.py` daily log). If off-nominal, replan remaining days.
4. Log any anomaly flags (see below) and escalate per severity.

## Anomaly Response

### Overcurrent (current > nominal + 40%)
- **Immediate action:** command thruster to standby if current remains
  elevated for more than 2 consecutive samples.
- **Likely cause:** PPU fault, cathode conditioning issue, short.
- **Escalation:** notify thruster hardware supplier if event recurs
  more than once per day.

### Thermal runaway (temp rise > 5°C/hr sustained)
- **Immediate action:** reduce duty cycle or safe the thruster if rate
  continues to climb; verify radiator/thermal control telemetry.
- **Likely cause:** degraded thermal path, unexpected duty cycle,
  environment change (beta angle drift).
- **Escalation:** hold next burn window pending thermal review if
  temp approaches qualification limit.

### Thrust dropout (thrust < 20% of nominal during expected burn)
- **Immediate action:** confirm command state (was a safing triggered?);
  check propellant flow / valve telemetry.
- **Likely cause:** momentary fault, safing event, propellant supply
  issue.
- **Escalation:** if dropout persists beyond one pass, treat as a
  contingency and replan the remaining campaign with reduced
  available burn time.

## Verification Checklist (pre-campaign)

- [ ] Delta-v budget confirmed against propellant remaining
- [ ] Thruster health check passed (last ground test / in-orbit checkout)
- [ ] Ground station pass schedule confirmed for campaign duration
- [ ] Anomaly thresholds reviewed against current mission phase
- [ ] Collision avoidance / conjunction screening cleared for planned trajectory