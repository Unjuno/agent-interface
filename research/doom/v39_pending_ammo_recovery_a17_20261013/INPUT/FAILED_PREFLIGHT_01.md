# Preserved construction preflight 01

Command: `python -m unittest -v test_a14_pending_ammo_staleness`
Outcome: 1 passed, 1 failed. The changed-ammo case passed: prompt ammo 6, returned action after pending interval, current ammo 4/sequence 11, rejected `ammo_minimum_failed`, no executor admission or authority. The positive-control fixture failed because the fake client left current observation at source sequence 10 instead of publishing the required fresh sequence 11 after the turn. This is a fixture defect, not evidence against the controller predicate. No WSLc/formal run occurred on this version. The corrected source and its final one-time preflight/run are separately identified; this first outcome is not overwritten.
