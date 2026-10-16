# Shared pointer backend candidate — 2026-09-13

`session_v9.py` integrates `input_owner_v5.py` with the existing `executor_v3.py`.
The promoted/pinned `interactive_v10.py` baseline remains unchanged. This is a
core-semantics candidate, not a freeze qualification or measured speed improvement.

The new operations are absolute `pointer_move`, `pointer_click`, `pointer_drag`
and vertical `pointer_scroll`. Snapshot records include active client surface,
focused descendant and client geometry before/after image capture. Matching
samples bind the next program's authority once, including when its first step is
`observe`; a later observation cannot renew that program's target/geometry.
Matching samples do not prove atomic capture or exclude changes between samples.

The complete program is validated before input: observed-root integer points,
buttons 1–3, 2–32 drag points, click duration 1–250 ms, drag duration 1–5000 ms,
nonzero vertical ticks −10…10, and combined declared hold/wait duration ≤10 s.
The existing 1–16 step bound, deadline, latest-sequence and unique-id checks apply.
Planner-supplied surface/geometry fields are rejected. Actual execution includes
I/O and capture overhead; declared durations are not hard wall-clock guarantees.
Pointer cleanup uses the same independent owner and verified terminal release.

## Evidence, including failed starts

Four private-window integration launches are retained in `results/pointer-backend-*`:

| Cohort | Probe | Outcome |
|---|---|---|
| 01 | `pointer_backend_probe.py` | Fixture window timeout before backend initialization; empty result list |
| 02 | `pointer_backend_probe_v2.py` | Same timeout; explicit error recorded |
| 03 | `pointer_backend_probe_v3.py` | Ten checks passed, seven exact observations |
| 04 | `pointer_backend_probe_v4.py` | Window timeout despite WM property readiness; completed-drag addition never reached |

Cohort 03 covers invalid-tail prevalidation, stale sequence, expired admission,
combined budget, target injection, real click/wheel/key delivery, cancelled-drag
release, refusal to renew old geometry inside a program, and fresh-program recovery.
The failed fourth launch records an unmapped client, root parent, and running
Openbox. Its root cause remains unresolved; adding WM name/class/readiness did
not establish a fix. These launches must not be reported as four passing runs.
The diagnostic map-state interpretation follows the
[Xlib window documentation](https://python-xlib.github.io/python-xlib_20.html).

The subsequent [OpenTTD self-use](../openttd_task/SELF_USE.md) successfully exercised
the same backend in a real application, including a completed drag and independent
task score. That single success does not repair fixture reproducibility.

## Remaining gates

- Resolve managed-fixture startup and repeat bounded integration regressions.
- Broader desktop/DOOM regression, new-task/fresh-case comparison, multiple resets.
- Current drag snapshots occur after release; continuous mid-drag observation and
  replanning remain absent. This is not a real-time live-control solution yet.
- Latest sequence and matching geometry do not establish fresh post-cancel pixels;
  observation age/action ordering needs an explicit contract before promotion.
- Add region/task-relevant readiness evidence for animated applications. Full-frame
  pixel quiet remains a bounded observation helper, not semantic completion.
- Owner timeout/disconnect still requires supervisor cleanup as documented in
  [POINTER_LIFECYCLE.md](POINTER_LIFECYCLE.md).
