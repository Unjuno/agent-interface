# Issue #7424 A03 — bounded PI-state handoff

**Disposition: continuity pass with a tracking tradeoff; overall preregistered gate failed.** This is a new allocation after A02, not a rerun. The complete preserved evidence is in this directory.

## Frozen question and method

A03 replaced A02's held additive offset with an online-updated PI integral state and conditional anti-windup. It asked whether seeding the receiving controller from actually applied input could reduce the first command discontinuity by at least 25% without worsening finite-horizon tracking error.

The scalar plant was `y[t+1] = y[t] + 0.25 * (u[t] - y[t])`. Controller parameters were `Kp=2`, `Ki=0.1/tick`, integrator-state clamp `[-1,1]`, output clamp `[0,1]`, output slew `0.2/tick`, and 20 updates. The conditioned initial integral state was `z = u_applied - Kp*(reference-y)`; cold start used `z=0`. The integral state updated by `Ki*error` unless that update would drive further saturation. Tracking utility was the sum of absolute errors over 21 samples. Settling, if reached, required three consecutive samples with absolute error at most 0.05.

Frozen cases: no disturbance `(y=0.4,u_applied=0.6)`, step disturbance at switch `(y=0.5,u_applied=0.6)`, and saturation `(y=0.5,u_applied=1.0)`, all with reference 1.0.

## Result

| Case | Cold first jump | Conditioned first jump | Cold 21-sample IAE | Conditioned IAE | IAE gate |
|---|---:|---:|---:|---:|---|
| No disturbance | 0.20 | 0.00 (100% lower) | 6.0238 | 8.4505 | Fail (+2.4267) |
| Step disturbance at switch | 0.20 | 0.00 (100% lower) | 5.65 | 7.38 | Fail (+1.73) |
| Saturation at switch | 0.00 | 0.00 | 5.60 | 5.60 | Not eligible for continuity contrast |

Thus the dynamic PI state achieved continuity in both eligible cases, but the preregistered no-worse-IAE requirement failed in both. It did not establish a useful dynamic-continuity solution. Saturation erased the contrast. No overall PASS is claimed.

## Independent checks and controls

The separately run `audit_a03.py` independently recomputed the saved traces and metrics and checked source hashes, state bounds, the continuity margin, denied stale/missing/revoked/pre-quiescence transfers, delayed handoff ordering, and mutation sensitivity (including requested versus actually applied input). All these checks passed. Only the two eligible no-worse-IAE checks failed. Audit classification: `CONTINUITY_PASS_TRACKING_TRADEOFF`; `passed=false`.

The run used one CPU in WSLc with a cached pinned image (`python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`), `--pull never`, network disabled, read-only source, and separate output. WSLc warned that swap-limit support/cgroup was unavailable, so no memory-enforcement claim is made. This is a synthetic scalar model only: no application, game, GUI, planner, learned model, physical actuator, or task outcome was exercised.

## Reproduction and evidence map

`PRE-RUN.json` freezes the hypothesis, method, decision gates, limits, and source hashes. `run_a03.py` is the candidate; `audit_a03.py` is the independent saved-output auditor. `CANDIDATE_COMMAND.txt`, `CANDIDATE_OUTPUT.txt`, and `CANDIDATE_EXIT.txt` preserve the invocation and result. `container-out/RAW.json` is the unmodified candidate record. `AUDIT_COMMAND.txt`, `AUDIT_OUTPUT.json`, and `AUDIT_EXIT.txt` preserve the independent audit. `SHA256SUMS.txt` records hashes for the package files (excluding itself).
