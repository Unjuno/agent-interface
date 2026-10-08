# Whole-program held-key preflight repair

Parent #57; stacked repair of #8308 exact head `dae92e12097907e860f68d6ee22a10cb23ace442`.
Claim: https://github.com/Unjuno/agent-interface/pull/8308#issuecomment-6041652161

`text("ba", gap_ms=20)` expands into `text("b")`, a wait, and `text("a")`.
With `a` held, the old operation-local overlap check refused only after the `b`
press/release requests. Preflight now advances a private copy of the held-key
ledger across the entire expanded program and refuses the known collision
before focus, program input, or waits. The real cleanup ledger is unchanged.
Same-name releases/repeats use the originally held physical code. Existing
runtime overlap and keyboard-map-change checks remain in place.

## Evidence and scope

This is an ordinary source repair and regression test, not a formal allocation.
The tests call real core validation, pacing, backend preflight/execution,
keycode resolution, key-state/chord/text, and session dispatch. X11 requests
and readback are inert fakes; opening a native display is forbidden.

- Initial test run: 8 methods; 6 failed subcases and 3 errors. Three errors were
  test fixtures violating the core's same-program key-down/key-up contract.
  Failed subcases also exposed shared fixture state; both fixture problems were
  corrected before editing production code. The first test source/log is retained.
- Corrected RED against unchanged production: 8 methods; 7 failed subcases and
  1 unmapped-key error. The source hash matches `baseline-backend.py`.
- Same corrected tests after repair: 8 methods PASS. Their hash is unchanged
  between `red-corrected.receipt.json` and `green.receipt.json`.
- First wider run: 33 discovered methods, 4 errors (3 missing sparse-checkout
  imports; 1 map fixture mapped every key to the same physical code).
- Restored unchanged import closure; corrected the mapping fixture to keep the
  held letter distinct from the later chord, and initialized the unsupported-
  verify fixture's ledger. Focused final run: **70 methods PASS**.
- Workflow compileall entry for materialized core/X11 files, changed-file syntax
  compilation, and `git diff --check`: PASS.
- Actual local dependencies: Python 3.12.14, python-xlib 0.33, Pillow 12.3.0,
  NumPy 2.3.5 on macOS arm64. CI pins older Pillow/NumPy; this run does not
  claim an identical dependency environment.

Positive coverage includes released-before-text, saved physical release after
mapping loss, Shift borrowing, unrelated held keys, and session refusal cleanup.
A backend preflight refusal emits no program input; a session can still send
cleanup releases for previously held keys. This is not an application-effect
or latency claim. Preflight models successful earlier operations; OS errors,
later map changes, and uncertain release readback still use runtime guards and
session recovery. Physical alias ownership policy is preserved, not redesigned.

The consumed native six-cell result in #8339 remains **FAIL_OR_HOLD** and was
not repeated. The later Tk fixture diagnosis does not turn that original
application-effect failure into PASS. No VM, native display, model, or shared
runtime was used for this repair.

## Reproduce

With Python 3.12 and python-xlib 0.33, Pillow 12.3.0 and NumPy 2.3.5 available,
from a checkout containing this patch:

```sh
DISPLAY= python -B -m unittest -v runtime.backends.x11_v1.test_held_preflight runtime.backends.x11_v1.test_key_chord_held_modifier runtime.guarded_x11_v1.test_deadline runtime.guarded_x11_v1.test_input_dependency runtime.backends.x11_v1.test_mapping_boundary runtime.backends.x11_v1.test_text_plan runtime.backends.x11_v1.test_partial_execution
```

The existing X11 CI test command now includes both held-key test modules;
no new job or workflow trigger was added. Remote/native CI was not rerun locally.
`evidence.tar.xz` preserves test iterations and source identities. MANIFEST hashes
refer to the published bytes; local path prefixes alone are normalized in logs.
Receipt stdout/stderr hashes retain the original private log identities.
Archived Python files are historical evidence and are not auto-discovered tests.

Author: root/e0cc, FINAL-v5. A distinct `preflight_review` worker statically
reviewed the design and working diff and reported no additional actionable
finding after the fixture corrections. That advisory is not a merge approval.
Fresh nonauthor content review and current-main combined-tree validation remain
required; no main or dependency-author branch update is part of this result.
