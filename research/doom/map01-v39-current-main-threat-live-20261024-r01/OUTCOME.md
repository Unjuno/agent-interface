# Current-main V39 WSL experiment outcomes

These are additive, bounded experiments on the user's PC in Ubuntu WSL2 with a private Xvfb + Openbox display. They are not evidence from a verified WSLc allocation. Each allocation has a frozen preregistration, retained raw output, and an immutable ID; failed IDs were not reused.

## Results

| ID | Outcome | What the evidence supports |
|---|---|---|
| `map01-v39-current-main-threat-live-20261024-r01` | Failed before any planner turn | V15 fixture setup and observation startup ran. The runner's strict JSONL reader stopped on an Xlib `xauth` warning printed to stdout. No model inference or task-control decision occurred. Final owner release reported empty keys. |
| `map01-v39-session-stdout-probe-a02` | Diagnostic confirmed the R01 failure cause | Six child stdout lines included one non-JSON Xlib warning. No app-server or model call. The session closed and the independent score was recorded. |
| `map01-v39-session-stdout-probe-a03` | Passed after the Xauthority fix | Six child stdout lines, zero JSON parse failures, initial observation and post-control score present, child exit 0. No planner or model call. |
| `map01-v39-current-main-threat-live-20261024-r02` | Partial live control; stopped safely | Two planner turns completed; five input admissions and five completed steps were recorded. Four explicit key-up events were verified by X11 keymap, and the cancellation release verified the remaining held key-up. All owner-release records ended with no down or unknown keys. Health stayed at 97; ammo changed from 48 to 46. The independent scorer sampled at about 35 Hz for 242 samples and reported 0 kills, no death, and no MAP01 exit. |

R02 stopped after cancellation interrupted a target-focus query. The query worker retired, and a later accepted action failed closed with `needs_decision` and zero completed steps. This is a useful release-safety result but demonstrates that the current caller does not recover within the same target-observer generation. The code follow-up makes cancellation take precedence over the interrupted query in the recorded terminal reason; it does not yet establish observer recovery. R02's raw record still reflects the pre-follow-up code and is not rewritten.

Ammo change is an observed environment response consistent with firing, not proof of a kill or task success. X11 server-keymap evidence is not physical-key verification. No MAP01 clear, reliability distribution, human-tempo timing, matched efficiency comparison, or cross-domain result is claimed.

## Provenance and validation

- R01 is pinned to `fd9f7be36806b088a2b7df7c17d2cd2e3b7ab174`; its preregistration SHA-256 is in `PREREG.sha256`.
- A03 and R02 are pinned to Xauthority fix commit `26c383a983782be25d6a1ae33814f7c551d88d63`; their source lists match that commit after accounting for the checkout's LF/CRLF representation.
- `audit_evidence.py` verifies all four preregistration digests, the pinned source bytes, the R02 event counts, release evidence, scorer result, and observed signal values. Its output is `RESULT.json`.
- The V39 JSONL startup fix and cancellation-reason follow-up passed 83 focused regression tests in Ubuntu WSL using the repository's Python 3.12 probe environment. The first broad test invocation hit a pre-existing `session_v7`/`session_v8` import shadowing collision; preloading `session_v7` from `research/live_control` resolved it, after which all 83 tests passed.
- `diagnostics/session-stdout-probe-a01` is an invalid preparation artifact and has no run result. It is retained and must not be interpreted as evidence.
