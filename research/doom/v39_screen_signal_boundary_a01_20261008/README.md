# V39 screen-signal boundary A01

This frozen synthetic construction probe isolates which current-main observations can stop an authored V39 cover while the planner is pending. It is not a live allocation and does not test DOOM, semantic threat recognition, policy quality, physical input release, useful feedback, or task success.

The frozen main revision is `a0d0602b89b1f5a05f851728fe90684ec4bfeff5`. The controller and typed signal guard Git blob IDs are recorded in `FREEZE.json` and matched the local current-main source used for the probe.

One advanced-epoch observation changed its frame hash while health stayed 100 and ammo 50. The current monitor returned no invalidation. A paired observation with health 79 below hard floor 80 returned `health:below_hard_minimum` and required a new decision without granting input authority. The result establishes a software capability boundary only: a changed screen hash alone does not currently stop the cover through this monitor.

A prior in-memory smoke check exercised the same two branches before this package freeze; it is disclosed in `FREEZE.json` and is not the recorded candidate. The packaged candidate was run once after the 01:48:15 UTC freeze timestamp. The independent auditor checks the retained result against the frozen H/T/D/C/U boundary and scope.

Run `python -B probe.py` to reproduce the candidate, then `python -B audit.py` to audit the retained `candidate-output.json`. `RUN_COMMAND.txt` records the original commands and source checkout location. `MANIFEST.json` hashes the package artifacts.

## Disposition

`PASS_CONSTRUCTION_BOUNDARY`: stable typed HUD plus changed frame hash preserves cover; a typed health hard-floor crossing requests a new decision. This does not establish that screen-only changes should cancel cover, that the old policy became unsafe, or that any semantic visual guard would improve task outcome. A live threat/recovery allocation remains necessary for those claims.