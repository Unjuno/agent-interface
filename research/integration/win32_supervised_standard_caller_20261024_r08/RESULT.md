# R08 result: construction abort before native input

R08 stopped in `source_preflight()` because its frozen `source_commit` used the abbreviated value `04af33158f`, while the probe requires exact equality with the full HEAD SHA `04af33158f617a1cdc2f867128ec569c71fdc80f`. The tracked tree was clean. The runner exited before creating `run/` or `raw.json`; no fixture started and no native input was sent. The failure is retained in `preflight_abort.json`. The frozen R08 conditions and code remain unchanged and this packet is not retried.

The next attempt must use the full source SHA before freezing. No WSLc or Docker allocation was used.
