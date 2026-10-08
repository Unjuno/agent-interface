# Excluded construction record

Formal invocations/rows at freeze: 0/0.

- construction-01: observer completed its 320 ms loop before the owner finished import/connect; audit correctly rejected missing spanning/post evidence.
- construction-02: added owner arm/trigger but owner still launched after observer readiness; same timing defect, audit rejected.
- construction-03: moved owner import/connect before observer measurement; all five conditions passed the draft audit and 12/12 corruption controls. This exposed ~1.7 ms / ~21 ms / ~24 ms / ~105 ms maximum round-trip stalls for healthy1/healthy20/kill20/watchdog100 respectively.
- construction-04: tightened healthy hold/stall lower-support checks before freeze; all five conditions passed, two contract tests passed, independent audit errors=[], 12/12 corruption controls rejected. Observed maximum spanning stalls: healthy1 1.679 ms; healthy20 20.689 ms; kill20 23.779 ms; watchdog100 103.757 ms. These construction values are excluded from the formal denominator and are not reliability estimates.

No threshold, condition, hold duration or formal row was changed from Issue #4297 to obtain these construction outcomes. The only construction repair was process/barrier ordering so the observer was active when the already-declared grab began.
