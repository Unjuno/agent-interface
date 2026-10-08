# Construction history

Smoke-0 failed before formal measurement: inherited TaskApp drift moved the nominal initial x=0.08 to observed ~0.129 before source capture, so the source-state gate failed. No measured comparison arm completed. The repair disables exogenous drift in this transfer fixture; source tolerance and all authority/guard/deadline/scoring thresholds remain unchanged.

Smoke-1 reached the owner-interruption path but the controller failed on `stop.flag` because its arm directory did not yet exist. Repair: create the output directory at controller start. No scientific condition or measurement threshold changed.
