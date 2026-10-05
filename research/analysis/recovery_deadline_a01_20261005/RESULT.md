# A01 result — Issue #8024

**Disposition: METHOD_PASS_SCOPED; comparative advantage over a fixed timeout not demonstrated.**

On the deterministic authored fixture, split-conformal calibration had `n=10`, `alpha=0.2`, rank `ceil(11*0.8)=9`, and deadline `9`. The nine nominal held-out recoveries were covered 9/9 (100%, above the 80% nominal threshold). No hard identity/focus/lease event was delayed. Five shifted-stratum episodes were returned `uncertified_yield`; one divergent and one right-censored evaluation yielded at the deadline. Small calibration and calibration censoring refused certification. The independent row oracle matched candidate deadline and coverage.

Comparator outcome: immediate latch retained 0/9 recoverable nominal episodes; fixed timeout 9 retained 9/9, exactly matching the calibrated rule on this fixture; dwell/hysteresis 2 retained 2/9. Thus the hypothesis's narrow comparison to immediate latch passes on this authored table, but the method adds no observed benefit over the simpler fixed timeout. No policy recommendation follows.

Mutation audit: evaluation leakage, hard-event label mutation, dropping the frozen right-censored row, and deadline continuation were rejected/detected. Shifted episodes were not counted toward nominal coverage and were marked uncertified. Normal and optimized-Python test runs each passed 11/11 after one retained test-fixture construction failure was corrected.

This is finite construction evidence, not a calibrated real-world deadline, exchangeability proof, GUI safety proof, live benefit, or permission to continue local autonomy. A next useful rung would be a preregistered finite simulator with generated exchangeable episodes and a separate known-shift stratum, independently audited; later GUI transfer requires its own authority/resource gate.
