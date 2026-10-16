# Observation recovery without silently renewing input authority

`session_v7.py` separates `observe`/`decide` execution from focus authorization.
A program binds its input focus once at its first step, including when that
binding is unknown. Observations may update the backend's latest state, but
cannot update the current program's binding. Input after an initially ambiguous
observation still requires a new program. `interactive_v8.py` wires this into
the research CLI. Expiry and cancellation remain enforced for observations;
this is not an unbounded or concurrent observation channel.

## Controlled comparison

Four private-Xvfb episodes (`focus-recovery-01`, two seeds, reversed arm order)
force an actual X11 focus transfer between image capture and context collection.
Both previous-backend episodes stop even an observe-only recovery request.
Both new-backend episodes capture again, then accept input under a fresh intent
bound to the newly observed destination. The destination deliberately is the
visible test sink, not the original XTerm; this validates explicit rebinding,
not automatic return to the original task window.

In both candidate episodes, a mixed `[observe, text]` program stops before text:
its new observation does not authorize its tail. The probe preserves destination
KeyPress fields and source hashes. Ten frames reconstruct exactly and match
PNG pixels. All terminal input-release checks passed. No saved-task outcome
is assigned to these controlled recovery probes.

## Actual assistant use

In `recovery-assistant-01`, the assistant used revision 8 to enter 222 in A1 and
440 in A2 in Calc, inspect the Excel-format dialog, confirm it, and inspect the
saved sheet. The first dialog image showed an unpainted window, so an additional
observation was requested before choosing the confirmation action.

After confirmation, capture-time focus samples naturally differed (1 versus
the worksheet window ID). The next observe-only request succeeded despite the
ambiguous binding. The assistant inspected the resulting worksheet; independent
workbook evaluation then confirmed A1/A2=[222,440]. Nine frames audited exactly.
Four programs completed with verified release, and owner shutdown also verified
release. This is a natural modal-transition recovery example, not just injected
state. It is still one exploratory assistant trial, not broad modal coverage.

The explicit recovery costs a planner/tool round trip. Matching focus samples
do not prove that pixels are fully painted or that a file is saved. Automatic
useful-observation selection, bounded modal handling, focus-check races and
matched planner timing remain open. The next iteration should reduce delivery
of not-yet-useful frames without replacing real completion evidence with sleeps.
No human-speed or token-saving result is claimed.

## Reproduce

Run in the documented Ubuntu/WSL environment from this directory:

```sh
python3 probe_focus_recovery.py --out ../../results-local/recovery-new
python3 audit_recovery.py results/focus-recovery-01
python3 audit_owner_sessions.py results/recovery-assistant-01
python3 interactive_v8.py --app calc --seed 940301 --out ../../results-local/recovery-session
```

Previous measured revisions remain unchanged. The interactive manifest covers
inherited GUI/codec sources; the controlled probe hashes its directly measured
runtime sources. Existing test-harness temporary-directory and X11 startup
cleanup limitations are unchanged.
