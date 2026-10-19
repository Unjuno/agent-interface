# A02 first live outcome

**Result: retained runtime failure; the hard threat-guard hypothesis remains untested.** The dedicated OrbStack arm64 VM ran the exact MAP01 threat-contact fixture once with current-main V39, `gpt-5.6-luna` at low effort, and the V15 per-key release measurement session. Four model turns completed before the controller stopped. The host independently verified all four model-image paths against guest receipts and SHA-256.

The typed HUD stream recorded health `97 → 91 → 85` and ammo `48 → 41`. Those health changes remained above the authored hard floors, so the run exposed soft-change handling but did not exercise hard health-guard invalidation. No stale-answer discard or recovery after a hard guard crossing can be claimed. The independent scorer recorded one kill, no death, and no MAP01 exit.

After the fourth model answer, normal cover cancellation ended with `ValueError: up_batch requires the active input lease` at the input owner. X11 keymap receipts nevertheless reported empty keys after cancellation. The controller rejected the terminal because its status was `failed`; cleanup was incomplete. The first failure is preserved, and this allocation was not retried.

The independent audit passes source/fixture/WAD identity, retained image custody, exact-frame reconciliation, accepted-program/terminal cardinality, empty-release evidence, and score consistency. `formal_pass` remains false because the controller stopped on the retained runtime failure. See [AUDIT.json](AUDIT.json), [FREEZE.json](FREEZE.json), and the SHA-256 inventory [SHA256SUMS.json](SHA256SUMS.json).

## Runtime qualification

This ran directly in the dedicated OrbStack VM, not a Docker container. Nested Docker was denied by the VM's cgroup-device BPF boundary; isolation was not weakened. Full raw images and transport artifacts remain in the ignored local output directory `results-local/doom/map01-v39-live-threat-guard-a02-20261009/`; the manifest inventories every retained file. Key event, owner, scorer, and model-protocol traces are copied into `raw_traces/` for review.

The separate A01 harness launch stopped before source freeze, game startup, or model call because the host runner tried to read a VM-only WAD path. Its prelaunch failure is retained under `results-local/doom/map01-v39-live-threat-guard-a01-20261009/` and was not overwritten.
