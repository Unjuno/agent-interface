## A02 posthoc addendum

This is a posthoc count over the A14 protocol-deviation trace, not a preregistered or live result. The pinned stream contains 170 typed observations and 169 adjacent pairs. The whole-frame RGB hash changed in all 169 pairs; in 153 pairs both typed health and ammo remained unchanged. Health changed in 10 pairs and ammo in 6 (these counts can overlap).

This warns against using a raw whole-frame hash delta as a direct cancel predicate: in this single retained exploratory trace, it would fire on every adjacent observation, including many pairs with unchanged typed HUD. It does not establish that any of those visual changes were task-relevant, occurred during active cover, or made the cover inappropriate. The analysis explicitly does not correlate against planner-pending or cover-active intervals.

`analyze.py` extracts only observation ID, sequence, capture time, frame hash, health, and ammo after verifying the full event-stream SHA-256. `audit.py` independently recomputes the adjacent-pair arithmetic from that reduced trace. A14's protocol deviation status remains in force.