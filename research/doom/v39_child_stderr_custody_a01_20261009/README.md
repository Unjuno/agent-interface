# V39 child-stderr failure custody A01

## H/T/D/C/U

**H — Hypothesis.** When the V39 session child exits before `ready`, the controller preserves the startup exception but loses the child diagnostic because it reads `stderr.txt` only on the normal completion path. The failure cleanup should retain the child stderr prefix without allowing a stalled pipe reader to block cleanup.

**T — Treatment.** On current main `771e8696b66deb18b4b3baf14e1ab8e2bc537edf`, add a regression using a real local Python child that writes a diagnostic and exits before readiness. A second controlled stream holds the stderr reader open to check bounded cleanup and that a timed-out stream remains open.

**D — Decision.** The failure regression retains the exact diagnostic in `stderr.txt` and records capture status in `controller-failure.json`. The bounded-reader regression returns within its limit, records an incomplete capture, and leaves the active stream open. The paired controller-cleanup suite passes in normal and optimized Python; see `normal-tests.txt`, `optimized-tests.txt`, and `FREEZE.json`.

**C — Controls.** This is a local construction test of `ControllerFailureCleanup`. It does not invoke Codex app-server, ViZDoom, a game, a model, a VM, GUI, or native input. A04 files remain immutable; no allocation is retried.

**U — Limits.** This repair preserves future child diagnostics but does not identify why the A04 child exited. Capture is capped at 1 MiB. If the pipe does not reach EOF within one second, the receipt marks it incomplete; the stream is not closed under a live reader. This provides no live-control, model, game, input-release, or task-effect evidence.

## Reproduction and verification

The first regression was run against the unmodified helper and failed because no failure-path `stderr.txt` existed. After the repair, run:

```text
python3 -B -m unittest test_controller_failure_cleanup_v1 test_controller_failure_cleanup_v39 -v
python3 -O -B -m unittest test_controller_failure_cleanup_v1 test_controller_failure_cleanup_v39 -v
python3 -B -m py_compile doom_controller_failure_cleanup_v1.py test_controller_failure_cleanup_v1.py test_controller_failure_cleanup_v39.py
git diff --check
```

The first auditor output is retained as `AUDIT_INITIAL_FAILURE.json`: its test-log predicate assumed a different unittest spacing and falsely marked both new cases absent. The auditor now checks test-name prefixes and passing line endings; the corrected result is in `AUDIT.json`. The test logs and frozen source hashes were not changed. `SHA256SUMS.txt` binds the retained package files.
