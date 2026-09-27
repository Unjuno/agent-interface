# Preregistration — application-effect vs render-only control

Parent: Issues [#3240](https://github.com/Unjuno/agent-interface/issues/3240),
[#2850](https://github.com/Unjuno/agent-interface/issues/2850), and
[#2606](https://github.com/Unjuno/agent-interface/issues/2606).

## H / T / D / C / U

**H** — A real Ctrl+S application-state transition and a visually persuasive
fixture-rendered decoy can be distinguished only when effect evidence is bound
to the original GTK application/window identity and input trace. A visual or
pixel-only “saved” judgment will falsely accept the decoy; an independent
evidence-bound audit must reject it.

**T** — Use the current-main GTK fixture and public golden-v3 X11 adapter in
two fresh private Xvfb sessions, fixed order:

1. `APPLICATION_SAVE`: enter `gtk3240` through the adapter, capture the same
   target window immediately before Ctrl+S, dispatch Ctrl+S, then retain the
   app effect file, app event log, before/after target XWD images, adapter
   receipts, target XID/PID/title/geometry, release receipts and process cleanup.
2. `RENDER_ONLY_DECOY`: leave a fresh target application untouched, create a
   second GTK window with the identical title and geometry that displays
   `saved:gtk3240` without sending Ctrl+S to the target app, and retain both
   window identities and XWD images, app event/effect evidence and cleanup.

Run the independent standard-library auditor in a separate container
invocation over the completed raw bundle. No reruns or replacements. Freeze
the current-main commit, all runner/auditor/fixture/Dockerfile hashes, image ID
and package versions in `FREEZE.json` before the two-session invocation.

**D** — `PASS_APP_EFFECT_DISCRIMINATED` only if the real arm has the exact
`{"saved": true, "text": "gtk3240"}` application effect, a save event,
unchanged target XID/PID/title/geometry, changed target-window pixels, a
completed adapter receipt and verified empty input release; the decoy arm must
show a saved-looking, changed image from a different XID/PID with identical
title/geometry while the original target XID/PID/image remains unchanged and
has no save event/effect file. The independent audit must accept the real arm
and reject the decoy. Missing or contradictory evidence is `HOLD`/`STOP`, never
PASS. A naive visual-only positive on the decoy is reported as a negative
control result, not as task success.

**C** — Docker Desktop Linux/amd64, pinned Python base digest
`sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`,
GTK3/PyGObject, python-xlib and Xvfb. Runtime containers use `--pull=never
--network none --read-only`, read-only source, bounded tmpfs and a fresh
evidence mount. No model/provider/network call. One private GTK save action is
permitted only in the positive arm. Preserve construction failures unchanged.

**U** — Two diagnostic rows, one GTK fixture and one decoy renderer. This
does not complete #3240, satisfy the full eight-case #2606 matrix, or establish
general GTK/app correctness, model utility, efficiency, human tempo, production
readiness or broad desktop reliability.

## Integrity boundary

The prior #2850 result and its raw/history are not changed. The older
`formal_matrix_runner.py` remains a receipt-emission preflight: it preassigns
delivery/effect/cleanup, synthesizes refusal event rows, and declares itself
not formal #2606 acceptance. This rung does not reuse its synthetic dispositions
as live observations.
