# Issue #8577 A01 — real-widget lens-law transfer

## Allocation and scope

Run ID: `8577-real-tk-lens-law-a01-20261008`. This is a fresh, bounded transfer test succeeding the finite simulator in closed #8556 / merged PR #8558. Those records remain unchanged. The source is frozen against current main `0e50fc59a737f58cb72db5bac4a5d845df00badf`.

The GUI boundary is a disposable Tk 8.6 fixture mapped inside a private Xvfb display in the pinned local WSLc image `ai-x20-tk-5260:20261003-a02` (`sha256:217851fe68e7340cd6301e6d1a1bd79d2c7b6cb4d13eb444a06fabaf0fde3417`). The adapter sends generated keypress/key-release events through Tk's real event queue and default Entry/Checkbutton bindings, services the Tk event loop, and reads back actual widget values, status text, focus, epoch, and completion receipts. Input is synthesized at the toolkit boundary; this is not physical keyboard injection, an OS-control backend, or a production application. No network, model, user data, external service, or persistent application effect is used. This uses WSLc isolation and does not require Docker Desktop or an external daemon. The image lacks `xauth`, so `xvfb-run` cannot launch; the frozen runtime directly starts Xvfb and sets `DISPLAY=:99`.

## H / T / D / C / U

**H — hypothesis.** On one isolated real-widget route using declared idempotent `set_text` and `set_checked` operations, scoped Get–Put / Put–Get / Put–Put checks identify seeded wrong-target, ignored-input, duplicate-callback, and first-write-wins defects that final-label or same-request replay alone can miss, while abstaining on stale epoch, pending completion, and focus ambiguity. A non-idempotent counter command is outside the law domain.

**T — treatment.** Execute the frozen 13-row case table in `input.json` through actual Tk `Entry` and `Checkbutton` widgets. Cases include valid text/check updates; an equal-value no-op; each seeded fault individually; a two-distinct-write sequence; stale-epoch, pending and completed asynchronous receipts; focus moved to a decoy; a non-idempotent command that must not be invoked; and a selected wrong-target × duplicate-callback pair. Every route starts from a fresh fixture. The weak same-request replay comparator repeats the same route from a fresh identical widget state and compares visible terminal state. The final-label comparator reads only the requested field, deliberately ignoring the visible status label.

Candidate observations are limited to the current field projection, visible status label, completion receipt, epoch, and focus. The independent auditor reads the separately retained raw widget values and ordered Tk callback/event log. The auditor does not import candidate or fixture code.

**D — decision.** `PASS_METHOD_SCOPED` only if the four valid controls pass; each applicable seeded fault is a law `VIOLATION`; stale, pending, and focus-ambiguous states are `UNKNOWN`; the non-idempotent operation is `NOT_APPLICABLE` and remains uninvoked; the duplicate-callback final field label and replay comparator both miss the seeded fault; every candidate row is reconstructed from raw widget/event evidence; and all four audit mutations are rejected. Any applicable fault passing, valid control failing, out-of-domain case passing, raw event/state contradiction, or independent audit error is `FAIL_METHOD`. A missing/malformed GUI readback or completion receipt is `HOLD_REAL_WIDGET_ORACLE`.

**C — competing explanations.** The prior finite laws may not add practical detection beyond a strong route-specific receipt checker; Tk's deterministic bindings may make this fixture easier than a real toolkit/application; and visible callback status may overstate what an actual agent-facing view exposes.

**U — uncertainty.** One small Tk fixture, one Linux/WSL/Xvfb stack, authored deterministic faults, and synthesized toolkit events only. This does not establish natural defect prevalence, arbitrary GUI/lens conformance, OS-level input delivery, accessibility-tree correctness, task completion, safety, portability, or product readiness.

## Frozen invocation and stop rule

Construction tests must pass before the freeze commit. Then invoke the candidate exactly once, creating only `results/candidate_raw.json`. If and only if it exits successfully, invoke the independent auditor exactly once, creating only `results/audit.json`. No retries, tuning, source repair, or overwrite under this run ID. Preserve the first failure/STOP/HOLD and allocate any repair under a distinct successor only after retaining it.

From the package directory:

```text
Xvfb :99 -screen 0 1024x768x24 -nolisten tcp >/tmp/xvfb.log 2>&1 &
sleep 1
DISPLAY=:99 python3 -B candidate.py --input input.json --output results/candidate_raw.json
DISPLAY=:99 python3 -B auditor.py --input input.json --candidate results/candidate_raw.json --truth truth.json --output results/audit.json
```

The independent audit reads saved raw Tk widget state and callback order; it does not rerun the candidate or relaunch the GUI. The output paths use exclusive-create semantics.
