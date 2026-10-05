# A01 freeze — Issue #8024

- Issue: #8024, calibrated recovery deadlines for transient soft-signal mode retention.
- **H:** On the frozen finite fixture, conformal deadline retains more recoverable nominal cases than immediate latch, meets >=80% held-out nominal coverage and delays no hard event; fixed timeout or hysteresis may perform as well.
- **T:** Enumerate nominal recovery cases, a diverging case, right censoring, three hard events, and an out-of-stratum evaluation set; compare immediate latch, fixed timeout 9, dwell 2 and split-conformal deadline; independently recompute every frozen row; apply the five Issue-specified mutations.
- **D:** `METHOD_PASS_SCOPED` only for exact oracle agreement, nominal coverage >=0.8, zero hard delays and detection/refusal at every mutation. No superiority claim if fixed timeout matches.
- **C:** Immediate latch, fixed timeout 9 and dwell/hysteresis 2.
- **U:** Authored fixture only; no empirical exchangeability, real controller dynamics, GUI semantics, or live task effect.
- Scope: T0 method construction only. No model, GUI, application, OS input, GPU, network, or live allocation.
- Runtime: WSLc container `agent-interface/native-suite-wslc-a08:20261004`; Python from that image; 1 CPU requested, 512 MiB requested, read-only bind mount. WSLc warns cgroup/swap memory enforcement is unavailable.
- Candidate inputs: deterministic finite fixture in `experiment.py`; calibration recovery times `[1..10]`; alpha `0.2`; split-conformal one-indexed rank `ceil((n+1)*(1-alpha))`; evaluation nominal recovery times `[1,3,5,7,9,2,4,6,8]`, one divergence, one right-censored case, hard identity/focus/lease losses, and five explicitly shifted episodes.
- Comparator controls: immediate latch (retained recoverable episodes 0), fixed timeout 9 (nominally retained 9/9), and hysteresis/dwell 2 (2/9). No parameter tuning after observing outcomes.
- Gates: exact rank/deadline reconstruction; nominal held-out coverage >=0.8; zero delayed hard events; out-of-stratum evaluations explicitly uncertified; small n and censored calibration return no finite certificate; independent row oracle checks IDs, labels, split, decisions and coverage.
- Mutation checks: calibration/evaluation leakage; hard-event relabeling; dropped censored evaluation row; shifted evaluation stratum; continuation after deadline.
- Limit: this authored finite fixture is not an empirical sample from any application and cannot establish conformal exchangeability outside the fixture.
