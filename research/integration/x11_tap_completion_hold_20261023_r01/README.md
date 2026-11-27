# Matched single-key completion-hold comparison — R01

**PASS_COMPLETION_HOLD_DISCRIMINATOR_SCOPED.** Four predeclared native WSL2/private-Xvfb cases completed in ABBA order with two samples per method. Both prior-method cases left `a` down during the injected completion hold and produced ten counted handlers. Both repaired-method cases were already up during that hold and retained one handler. All cases completed the public input/close and ended with a fully neutral independent keymap. No formal arm or whole attempt was retried.

| Case | Method | Key during hold | Count at hold start → end → final | Completion hold (ms) |
|---|---|---|---|---:|
| 0 | Prior | DOWN | 1 → 10 → 10 | 1005.571280 |
| 1 | Repaired | UP | 1 → 1 → 1 | 1007.249239 |
| 2 | Repaired | UP | 1 → 1 → 1 | 1006.448918 |
| 3 | Prior | DOWN | 1 → 10 → 10 | 1007.108662 |

Intervals are monotonic-nanosecond endpoint differences converted to milliseconds. The held sample interval was at least 1000ms in every case. Public call intervals were 1054.186–1062.655ms, intentionally dominated by the imposed gate. These observations are not a speedup estimate, a model/token-economics measurement or a reliability distribution.

## What was compared

Both arms use current caller/guards/fixture source from main `e0d0cdb5108460842f3c5901f6cd2b501bc26cf4`. For the prior arm only, the two exact `key_state`/`key_chord` function ASTs from `6e7f88d2dc389ebb96b7e6921fb5cd0e84da71ec` are substituted in memory. The full original [backend blob](baseline_backend.py.txt) is retained; no production file is rewritten. The repaired arm uses the current methods. This isolates the two-method change rather than comparing unrelated repository snapshots.

Source/auditor freeze: `b51e42726`; conditions freeze: `83f9b4a3b` before the single attempt marker. [conditions.json](conditions.json), [219 source identities](SOURCES.json), [all dependency versions](pip-freeze.txt), preflight, [runner](run_probe.py), [host command/exit](host-launch.json) and `run-result.json` retain actual scope. The caller is `create_server(..., session_mode='guarded-x11', guarded_process_identity=True)`, same-process guarded owner; it is not the owned-process/prestarted-cancellation mode. The public observe/mint/input/results/close path is used, and exact messages/native reports/images remain under each case directory.

## The injected boundary and independent reads

The wrapper first calls the actual Xlib `Display.sync()` and waits for its real reply, then withholds completion to the backend. It does this once after the first target DOWN. This is a **client-facing completion hold after a real roundtrip**, not a missing network reply, blocked request send, stopped X server or earlier delayed XTEST request.

At hold entry, raw request prefixes contain only DOWN for prior methods and DOWN/UP for repaired methods. Both retain `{'a':38}` as a possible-DOWN obligation until completion is returned, even when the independent keymap already shows UP. A separate fixture X client increments an X property per handled KeyPress; a separate observer X client samples that property and keymap before input, twice during the hold and after completion. The two during-hold snapshots are at least1000ms apart. Their count agrees with the complete retained handler trace at the end.

The prior cases show extra application presses without additional producer DOWN requests during the hold. All four fresh servers report identical enabled keyboard-repeat controls; automatic repeat is consistent with the data. The result does not attribute every possible production repeat or prove arbitrary non-idempotent external task outcomes. No repeat setting, task definition or input guard was weakened.

The [independent read-only auditor](audit.py) was frozen before execution. Its [47 checks](audit.json) reconstruct literal prefix/state/count/obligation ordering, exact control equality, public completion and owned cleanup without importing runtime or its scorer. A passed discriminator supports this particular completion-boundary repair; it does not turn the prior ten-handler task into success.

## Isolation, cleanup and limits

One job on two inherited logical CPUs, nice+10; four fresh authenticated owned Xvfb domains sequentially on `:188`, TCP disabled, new cookie per case. No model calls, WSLc/Docker allocation, Windows desktop input, package install during the trial or shared-runtime inventory. Each server was resumed/terminated through its own retained pidfd and reaped with exit0. A separate [cleanup readback](cleanup-recheck.json) found all four owned server PIDs (394,405,415,425), lock and pathname socket absent. Fixture threads stopped; final independent keymaps were neutral. Private auth cookies were removed; Xvfb warnings are preserved.

ABBA reduces a simple order drift but does not remove all confounding; two samples per method are not broad reliability. The fixture count is a synthetic handler/effect proxy. No cancellation or recovery supervisor is invoked in this schedule. Sending DOWN/UP can still block or be interrupted between requests; a delayed request ahead of UP can still cause repeated effects. Physical/MAP01 control, broader target fencing/recovery authority, provider/model integration and matched efficiency/reliability remain open. The earlier stalled-server/held-key failures remain unchanged.
