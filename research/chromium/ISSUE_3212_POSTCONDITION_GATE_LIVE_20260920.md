# Issue #3212 — live contradictory/absent DOM postcondition gate (2026-09-20)

Additive fail-closed evidence. Existing results and HOLDs remain unchanged.

## H/T/D/C/U

- **H:** Transport/input dispatch success must not be treated as an application success when the independently observed DOM postcondition is absent or contradictory.
- **T:** Three real Docker `--network none` allocations using `mixed-formal-2992-debian:20260920`, Xvfb, real Chromium, and CDP DOM observation. The fixture's save handler was disabled before dispatch; the runner still issued the input/click and then evaluated the independent DOM postcondition.
- **D:** `PASS_POSTCONDITION_GATE_AUDIT rows=3 errors=0`. Transport success `3/3`; expected postcondition `0/3`; admission `0/3`; DOM effect `0/3`; all three rows were classified `contradictory_or_absent_dom`. Raw SHA-256: `15fa613de6756c8a88a26030d44d5af6ef27f60b7126e0810528963a8c8b8815`.
- **C:** `PASS_CHROMIUM_POSTCONDITION_GATE_FAIL_CLOSED_SCOPED`. The live fixture does not accept a transport-only success without the independent application/DOM effect.
- **U:** This tests the declared DOM postcondition boundary only; it does not establish semantic correctness of every application oracle or resolve the full reuse-benefit HOLD.

Runner, fixture, raw trace, and independent auditor are under `research/chromium/issue-3212-postcondition-gate-v1/`.
