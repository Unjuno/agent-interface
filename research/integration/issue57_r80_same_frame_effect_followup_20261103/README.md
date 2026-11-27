# r80 same-frame Save effect follow-up

Date: 2026-11-03. This is a read-only analysis of the retained r80-a6 attempt
plus an offline regression for a narrowly scoped adapter correction. It does
not amend the original experiment, turn r80-a6 into a pass, or authorize replay.

## Retained attempt evidence

The source packet is
[`r80-a6`](../issue57_ocr_frontier_replication_20261103_r78_r83/r80-a6/README.md)
inside the hash-manifested R78–R83 archive. Its `compiled-result.json` records
`SAFE_YIELD/no_progress` after two completed transitions. The `enter` and `save`
transitions both report verified release. The last two observations are
sequences 13 and 18 and have the same digest
`5c0cb9612471da938311170129bb2c1c8b5abfcce00d1b17d2c74fae7259f09f`; both
have `cells_filled=true`. The top-level `task_save_request` is null and the
critical events contain no Save `effect_checked` record. The frozen graph
returned from its identical-digest `no_progress` branch before calling the
application effect verifier.

This explains why that attempt did not retain the profile's Save-request
receipt. It does **not** establish why the pre-close artifact check read the
blank-admission SHA (`b9c3744304b6f13c7804aa1ad1fe1e18384f6c53bf058975c05eae5139637d4f`)
with `populated_cell_set_mismatch`, nor whether the later populated FODS file
was durably written before that check. The later file and post-task screenshot
are separate evidence and do not repair the failed pre-close check. The packet
also retains a container exit code of 1 and an unknown parent task result.
r80-a6 remains failed under its frozen all-gates rule.

## Offline correction and composed regression

At current main `383562acd71b97ab67152807c9d043b199e49d60`, the compiled graph
uses `SAFE_YIELD/no_progress` by default for an unchanged evidence digest. That
default remains unchanged. A caller must explicitly provide
`verify_unchanged_effect`; the guarded X11 adapter requires the same observation
sequence and target association before passing it a private copy of the current
evidence. The registered Calc profile opts in for the Save action only, records
the request marker, and returns `unavailable`. Thus the marker records that the
profile reached its Save verifier; it does not prove save completion or task
success.

The adapter-level regression in
`runtime/guarded_x11_v1/test_compiled.py::test_unchanged_frame_save_uses_opt_in_callback_and_stays_unverified`
uses a Fake X bridge and the real graph/adapter composition. It presents a
changed frame after entry and an unchanged frame after Save while the fixture's
read-only predicate advances. The test requires the opt-in Save callback,
`SAFE_YIELD/effect_unavailable`, two verified releases, a retained
`unchanged-effect` record, and no task-success outcome. The existing core
no-progress regression continues to check the default opt-out path; the Calc
profile unit regression checks that the receipt is recorded only for Save.

Current focused local result:

```
python -m unittest runtime.guarded_x11_v1.test_compiled.CompiledX11Tests.test_unchanged_frame_save_uses_opt_in_callback_and_stays_unverified runtime.core_v1.test_compiled_gui.CompiledBoundaryTests.test_unchanged_frame_uses_explicit_nonvisual_effect_verifier runtime.core_v1.test_compiled_literal_unknown_01a0ff35
Ran 9 tests — OK
python -m unittest runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_registered_calc_profile_runs_through_owned_mcp_and_releases
Ran 1 test — OK
python -O -m unittest runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_registered_calc_profile_runs_through_owned_mcp_and_releases
Ran 1 test — OK
python -m unittest runtime.cli_v1.test_mcp_owned_process
Ran 72 tests — OK
python -m unittest runtime.core_v1.test_compiled_gui runtime.core_v1.test_compiled_literal_unknown_01a0ff35 runtime.guarded_x11_v1.test_calc_profile_v1 runtime.guarded_x11_v1.test_compiled
Ran 101 tests — OK
python -O -m unittest runtime.core_v1.test_compiled_gui runtime.core_v1.test_compiled_literal_unknown_01a0ff35 runtime.guarded_x11_v1.test_calc_profile_v1 runtime.guarded_x11_v1.test_compiled
Ran 101 tests — OK
```

The owned-process test drives the registered profile through the public MCP
route with the Fake X Save frame held unchanged; it confirms the marker reaches
the call-owned receipt while the graph still returns `effect_unavailable`.
These are offline tests. No live Calc attempt, live-provider API call, Docker pull, new
allocation, task-success claim, efficiency comparison, WSLc result, or MAP01
validation was produced. A fresh authorized execution and independent
pre-close scoring are still required to determine whether this improves the
live boundary; the full #57 cold/warm/invalidation/repair comparison remains
open.

The same adapter test, owned-process integration test, and synthetic
provider-wait/stale-source composition test also passed once each under normal
and `-O` Python in the cached `agent-interface-xvfb-mcp:late-input-r19` image
(`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`),
with networking disabled and 4 GiB memory / 2 CPU / 256 PID limits. The last
optimized provider-wait test needed a manual wake of `xvfb-run` after Xlib
successfully connected to the already-started Xvfb display; it then passed in
2.39 s. A fresh isolated container reproduced that wrapper wake condition and
also passed after the same display-verified wake. This is an Xvfb-run readiness
signal quirk in this image, not a product or Docker daemon failure. No image
pull or live application action occurred.
