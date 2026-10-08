# Issue #5970 T2 — prospective causal provenance on isolated X11

## Adjudicated result

**`HOLD_OBSERVER_EVENT_MISSING`** (candidate disposition: `HOLD_INCOMPLETE_OR_NONNEUTRAL`). The preregistered protocol required an explicit pair of app/observer event rows for each XTest transition. On the corrected T2c run, both sources acknowledged the actuation ID before dispatch; Tk recorded one `KeyPress` with the expected causal parent, but the independent X11 observer recorded no key event for that ID. The runner timed out and stopped before dispatching a release. The independent auditor reconstructed this result from the retained source streams and reported `PASS_AUDIT_HOLD_OBSERVER_EVENT_MISSING`, zero audit errors.

This does **not** demonstrate a complete causal cut or a positive traceability mechanism. It is a useful negative boundary: the pre-event arm/ack side channel alone does not prove that both event streams observed the same actuation. No timestamp was used to synthesize the missing edge.

## Attempt ledger

| Attempt | Outcome | Preserved evidence |
|---|---|---|
| T2 candidate v1 | `STOP_CANDIDATE_PREFLIGHT_INVENTORY_PREDICATE`; archive digest was intact, but code compared 324 regular files to 425 total tar entries (including 101 directories). No fixture or XTest input started. | `candidate.preflight_stop.raw.json` |
| T2b candidate v2 | `STOP` before dispatch. App and observer each wrote one arm ack; the runner polled `trace/app_events.jsonl`, but the app actually wrote `trace/tk/app_events.jsonl`. No XTest event was sent. | `candidate.v2.raw.json`, `run_v2/trace/` |
| T2c candidate v3 | One Shift `KeyPress` dispatched after both acknowledgements. Tk logged `app:1`, the actuation parent, keycode 50, and X time. Observer logged its arm ack but no matching event. Candidate stopped before release and did not query the terminal keymap. | `candidate.v3.raw.json`, `run_v3/trace/` |

The first two STOPs are retained unchanged. Candidate v3 is a distinct corrected runner and uses its own output directory; neither predecessor was edited or rerun. This probe is not a retry of the consumed #4135 formal matrix.

## H / T / D / C / U

- **H:** A serialized, explicitly armed XTest event can be observed by the independent X11 observer and Tk app with the same actuation parent ID, distinct source-local event IDs/sequences, and no timestamp-inferred causality. Missing or mismatched records must fail closed.
- **T:** Source-frozen #4135 fixture, instrumented app and observer, fresh isolated Xvfb display. Candidate v3 executed one Shift press and waited for both streams. Since the observer event was missing, the prescribed release step did not run. T2/T2b/T2c exact invocations and exits are in `RUN.md`.
- **D:** **HOLD**. There is one app event and zero observer events for the dispatched press; there is no release event or verified neutral terminal keymap. The independent auditor verified the HOLD from raw logs and frozen source/archive hashes. The candidate did not claim PASS.
- **C:** The input was sent only to an Xvfb virtual server under WSL2, not to the user desktop. After the runner exited, no Xvfb process was listed. The virtual server was torn down, but the terminal keymap was not queried; therefore neutrality is explicitly **unverified**. This environment had Docker Desktop's Linux engine unavailable, so the isolated host Xvfb fallback was used rather than a container.
- **U:** Why the observer did not record this XTest event; whether a different observation boundary such as XInput2 raw events can expose the same transition; concurrent/unsolicited event behavior; production integration and instrumentation cost; and whether any recovery decision improves remain unknown.

## Integrity and scope

The archived #4135 input is pinned to source commit `7625a3fc99f1da2099dc6e20e67383ee88c7f337`, archive SHA-256 `5f153824d677503275f268e2aef9c9971d5f0a3f369c573feaa1a5d10604ad8d`, 324 regular files, and 425 tar members. Candidate v3 and the independent auditor verified the archive parts and upstream `app.py`/`observer.py` source hashes. The 11 construction tests passed before candidate v3; Python compilation passed. Candidate v3 ran once and the HOLD auditor ran once. Exact raw bytes are checksummed in `SHA256SUMS.txt`.

**Method deviation / scope reduction:** the archived `app.py` and `observer.py` were used as pinned reference inputs, but T2c launched purpose-built instrumented test copies modeled on their Tk/Xlib structure. It did not mechanically transform and execute the exact archived files. Consequently the observed missing event characterizes this controlled replica's observer boundary only; it does not establish that the original #4135 observer loses an event. The next source-bound run must generate and hash an explicit patch against those archived files before any transfer claim.

Environment: WSL2 Ubuntu 24.04.4, Python 3.12.3, Tk 8.6, Xvfb 21.1.12, `python-xlib` with XTEST. Docker Desktop's service was stopped/manual and its Linux engine did not answer the installed CLI. No model, network, external app, or user's desktop was involved. This does not revise #4135, close #5970, establish production causal-consistent snapshots, validate authority, or show task benefit.
