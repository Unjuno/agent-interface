# Same-frame effect-verifier deadline gate

Date: 2026-11-03. Offline correctness repair against current `origin/main`
`43e48678faa841e880e0f512a35326bcbe2aee58` (same tree as tested branch base
`e6d4e239eb245e57050919b51b2c319555b2239a`).

## H/T/D/C/U

- **H:** A same-frame effect verifier must not begin after the compiled method's
  finite runtime deadline. The previous code checked the budget, did additional
  branch/effect work, and then invoked the callback without checking the clock
  at its start boundary.
- **T:** Use a deterministic clock calibrated to the callback-start read. Keep
  the earlier budget check before expiry, then return exactly the method deadline
  at the callback-start read. Exercise the unchanged-digest final Save path.
- **D:** PASS only if the callback is not invoked, the graph returns
  `SAFE_YIELD/budget_exhausted`, the two already-completed transitions remain,
  and the final Save effect stays pending. No replay or success claim is allowed.
- **C:** The callback is synchronous and read-only in this path; an already
  started callback can still overrun the method deadline. This change only
  prevents starting one at/after the deadline.
- **U:** The result is deterministic local semantics, not a real-time scheduler
  guarantee or live application result.

## Change

`runtime/core_v1/compiled_gui.py` now samples the monotonic clock immediately
before invoking either effect verifier and returns `SAFE_YIELD/budget_exhausted`
when that timestamp is at or beyond the method deadline. The receipt leaves
`effect_verification_started_ns` unset and preserves `pending_effect`; it does
not infer that the effect succeeded or failed. The regression drives the
unchanged-frame Save branch and verifies that its verifier is not started at
the exact boundary.

## Verification

- Windows Python 3.11.9: `runtime.core_v1.test_compiled_gui` plus
  `runtime.guarded_x11_v1.test_compiled`, **81/81** normal and **81/81** under
  `python -O`; `git diff --check` passed. Full output is retained in
  `windows-tests.txt`.
- Existing pinned Docker image
  `agent-interface-xvfb-mcp:late-input-r19`, ID
  `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`:
  same **81/81** normal and **81/81** optimized, network disabled, source mounted
  read-only, 4 GiB memory, 2 CPUs, 256 PIDs. Docker stayed responsive after the
  run. Full output and conditions are in `docker-tests.txt`.
- Source base and exact working patch are preserved in `source-base.txt` and
  `implementation.patch.txt`.

## Scope

This repairs one exact deadline edge in the shared compiled graph and closes a
missing offline regression at the same-frame verifier seam. It does not bound or
interrupt a callback that has already started, verify Calc's saved workbook,
change input-release semantics, or constitute live Calc, provider, WSLc, MAP01,
efficiency, or overall reliability evidence. Issue #57 stays open.
