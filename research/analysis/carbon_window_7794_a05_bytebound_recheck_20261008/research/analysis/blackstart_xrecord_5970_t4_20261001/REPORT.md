# Issue #5970 T4 — X RECORD delivery-boundary diagnostic

## Disposition

`PASS_RECORD_DISAMBIGUATES_OBSERVER_GAP` (single bounded synthetic trial; independent raw-payload parser). The T3-like selected-window observer recorded zero key events, while both the app and server-side X RECORD recorded one Shift press and one release (keycode 50). Both RECORD event timestamps matched their corresponding app event timestamps. Cleanup release was attempted and the terminal keymap was neutral.

The recording worker also ended with a Python-Xlib `TypeError("object of type 'NoneType' has no len()")` while the context was being disabled. This is retained in `candidate.raw.json` and `audit.raw.json`. It did not erase or alter the two already received raw 32-byte `FromServer` event payloads, which the independent parser decoded; therefore the result is a pass for the narrow delivery-boundary distinction, with a teardown STOP for library cleanliness.

## H / T / D / C / U

- **H:** X RECORD's server-side event stream can discriminate an X server-delivered event from a gap in the T3 window-selected observer.
- **T:** Same T3 exact-source-derived Tk app/observer, fresh private Xvfb, one Shift press/release, server-side RECORD of delivered core key events, unconditional release and terminal keymap query; independent parser/auditor.
- **D:** `PASS_RECORD_DISAMBIGUATES_OBSERVER_GAP` requires the RECORD raw payload, app, and observer streams to satisfy the frozen distinction and safety gates. Missing/ambiguous records HOLD; no time-based causal inference.
- **C:** One synthetic key pair and cooperative Tk window; private Xvfb host fallback because Docker Desktop engine was unusable. No physical/user desktop input.
- **U:** Cause of observer gap, RECORD perturbation/overhead, concurrent events, generalization, authorization, semantic truth, and product/task benefit remain unknown.

## Raw outcome

- X RECORD delivered core events: KeyPress(type 2, keycode 50, server time 26863547), KeyRelease(type 3, keycode 50, server time 26863579).
- App rows: 2; selected observer rows: 0; X RECORD rows: 2.
- Cleanup release attempted: yes; terminal Shift keymap neutral: yes.
- Candidate exit: 0; no app/runner error. RECORD callback teardown diagnostic: retained, as above.
- Independent audit: `audit.raw.json`, PASS. Candidate and raw streams: `candidate.raw.json`, `run/`.

This establishes that in this private Xvfb trial the server delivered the two synthetic core events while the selected-window observer saw none. It does not identify whether selection, propagation, subscription, scheduling, or the observer's queue handling caused the gap. It does not establish physical input, production behavior, causal provenance generally, recovery benefit, or user/task benefit; no causal edge is inferred from timestamp equality.

## Scope

T4 diagnoses the T3 measurement gap only. It does not revise T0-T3 or the original #4135 result, and it does not rerun a consumed formal allocation.
