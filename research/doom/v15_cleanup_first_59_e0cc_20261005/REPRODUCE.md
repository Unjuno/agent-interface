# Reproduction boundaries

This is an inert archive of ordinary synthetic regressions. No consumed formal allocation is replayed. Copy the archive to a fresh private directory before running its raw auditor, which writes `raw-audit.json` in the supplied directory:

```
python3 audit_raw.py.txt <copy-of-this-archive>
```

For a fresh synthetic controller run, select full01 (measurement-only owner) or full02/full03/full04 (final owner). Combine that run's parent and child loaded-source maps. Verify each SHA-256 against `source-closure.json`, restore its exact blob to `source/<original-path>`, and restore both `nonpython-source` files to `source/research/doom/`. Restore the run's probe_controller.py.txt, child_session.py.txt and fake_environment.py.txt as `.py` files alongside source. Use a new output name and Python 3.12 with Pillow and NumPy:

```
E0CC_TEST_CLEANUP_FIRST=1 python3 -B probe_controller.py <fresh-output> hard_change
E0CC_TEST_CLEANUP_FIRST=1 python3 -B probe_controller.py <different-output> unknown_change
E0CC_TEST_CLEANUP_FIRST=1 python3 -B probe_controller.py <different-output> failed_release
```

The shim delays only a cancelled UP-batch caller until the real owner thread records cancellation cleanup; it does not fabricate an owner/Session event or force a release. It is a deterministic schedule intervention, not a measurement of race probability or latency. All calls are bounded; fake external seams refuse network/native side effects. `failed_release` is expected to fail closed with a fake key still down.

For focused/adjacent unit regressions, use the complete repository tree at the recorded prior head, replace the two source files with final-input_owner_v12.py.txt and final-key_edge_measurement_v1.py.txt, and add final-test_input_owner_v12_cleanup_measurement.py.txt under research/live_control without `.txt`. The exact module list and PYTHONPATH order are in execution.json. Existing test definitions and dependencies come from that prior head; only the new cleanup test is added. Run normal and `-O` as separate processes. These tests need no native Xlib installation because their scoped fake displays provide it.
