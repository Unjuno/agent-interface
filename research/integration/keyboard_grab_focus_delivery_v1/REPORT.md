# Issue #4159 — active X11 keyboard grab versus focus-validated key delivery

Disposition: **PASS_KEYBOARD_GRAB_DELIVERY_BOUNDARY_SCOPED**.

## Result

One prospectively source-frozen private-X11 allocation completed 20/20 first-outcome cases, with zero formal retries, replacements, exclusions or post-freeze scientific tuning. The runner/supervisor and all per-case application/grabber processes exited zero; Xvfb was reaped and its socket removed; terminal X-server key/button observations were neutral.

| Policy / state | n | observed outcome |
|---|---:|---|
| FOCUS_ONLY / CLEAR | 3 | exact `7` delivered to A |
| FOCUS_ONLY / GRAB_BEFORE_PROBE | 3 | foreign grabber receives one press+release; no app text |
| FOCUS_ONLY / GRAB_AFTER_PROBE | 3 | same diversion |
| FOCUS_KEYBOARD_PROBE / CLEAR | 3 | probe succeeds; exact `7` delivered to A |
| FOCUS_KEYBOARD_PROBE / GRAB_BEFORE_PROBE | 3 | probe non-GrabSuccess; refuse before task key; zero effect |
| FOCUS_KEYBOARD_PROBE / GRAB_AFTER_PROBE | 3 | probe succeeds, later grab diverts one press+release; no app text |
| NO_TASK_INPUT | 2 | zero task key / app / grabber key effect |

The focus basis was A before each directed grab. The excluded construction established that an active XGrabKeyboard itself can make Tk `focus_get()` temporarily unavailable, so Issue #4159 corrected the original wording before formal execution. The experiment therefore measures the focus-check-to-key delivery interval rather than claiming focus stays currently observable under a grab.

## Audit

Raw-only audit: 225 checks, errors=[], decision PASS. Ten frozen evidence-control variants were executed; 9/10 rejected. The sole non-reject changes one nonzero refusal status to another nonzero refusal status and is semantically equivalent under the frozen contract. The preregistered decision gate required at least eight rejected corruptions. The ineffective control is retained; no postformal auditor rewrite or formal rerun occurred.

## H/T/D/C/U

- **H:** a prior focus observation does not guarantee subsequent key delivery if another X client takes XGrabKeyboard; a temporary grab probe detects an already-active grab but cannot close a later check/use interval.
- **T:** FOCUS_ONLY vs FOCUS_KEYBOARD_PROBE, CLEAR / GRAB_BEFORE_PROBE / GRAB_AFTER_PROBE, 3 repetitions each plus 2 no-task-input controls, private authenticated Xvfb.
- **D:** all 20 first outcomes match the frozen table; audit passes; 9 semantic/provenance corruption controls reject (>=8 gate).
- **C:** cooperative owner_events=false active keyboard grab; XTEST/X-server logical input; probe itself briefly grabs/ungrabs in clear cases.
- **U:** passive or owner_events=true grabs, IME/layout, arbitrary apps/toolkits, grab-owner authentication, model/task benefit, latency/tokens and production adoption remain untested.

## Integration meaning

Keep target/focus evidence, actual input delivery, release and application effect distinct. A successful focus check is historical evidence once another client can change keyboard routing. The candidate probe is diagnostic evidence for an already-active grab in this fixture, not a production default or atomic authorization mechanism.

## Retention

Formal raw evidence is stored losslessly as three ordered text parts declared by `PACKAGE.json`; `restore_formal.py` verifies each part, the combined encoded stream, decompressed payload, and every member hash before writing a fresh directory. This packaging is postformal and does not alter scientific source or results.
