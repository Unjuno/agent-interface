# Malformed auditor input probe — 2026-10-04

## Question and decision

**H:** A malformed X11 keymap hex field in otherwise valid candidate evidence can make the independent auditor raise instead of emitting an explicit failed/HOLD gate.

**T:** On the PR #7386 Windows/Python 3.11 construction fixture, replace one `after_admission` observer row's `keymap_hex` with `not-hex`, then call `audit.evaluate(freeze, candidate, events, observers)`. Run the exact probe first against the pre-fix auditor at `eb11a9d05e05e0c078ab5ac151d47cc6f47644ba`, then apply the smallest exception boundary and rerun the same test.

**D:** Confirm the hypothesis if the pre-fix evaluator raises and the repaired evaluator returns `FAIL_OR_HOLD_TELEMETRY_GATE`, with the malformed input marked failed. Do not treat the fixture's positive unmodified record as live telemetry evidence.

**C:** This is a deliberately malformed offline fixture; it does not imply that retained live evidence contains malformed hex. A schema validator before evaluation could also reject the input, but the current evaluator had no such guard.

**U:** No X11 server, input, game, model, container, formal allocation, or real candidate/raw record was used. The probe does not test event capture, per-key physical release, task feedback, recovery, matched comparison, or MAP01 outcome. The audit source change invalidates the old freeze's auditor hash; the consumed T0 remains untouched and cannot be rerun under that freeze.

## Result

At `eb11a9d05e05e0c078ab5ac151d47cc6f47644ba`, the mutation raised `ValueError` from `bytes.fromhex()` in the admission keymap check. After the guard was added, the same mutation returned `FAIL_OR_HOLD_TELEMETRY_GATE` with `audit_input_well_formed=false` and `audit_error_type=ValueError`.

Executed verification from this directory:

```text
python -B -m unittest test_candidate test_audit -v
Ran 12 tests ... OK
python -B -m py_compile candidate.py test_candidate.py audit.py test_audit.py
git diff --check
```

Both static checks exited successfully. The regression test captures the specific red/green result in `test_audit.py`.
