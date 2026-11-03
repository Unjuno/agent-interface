# Stale supervisor with replaced private-display authority

On 2026-11-01, two fixed-order WSLc allocations tested the experimental #10088
private Xvfb setup. Both started a real guarded owner and prestarted X11 cleanup
supervisor, retired that owner and its private display, then started a second
private Xvfb at the same display number. An independent fresh target received a
test-injected `b` press and the server keymap confirmed it was down. The test
then submitted a **synthetic** old `b` cleanup obligation to the old supervisor.
This is a direct supervisor test, not an end-to-end cancellation attempt.

| Condition | Supervisor | Fresh `b` after request |
| --- | --- | --- |
| Keep old authority | X connection rejected with invalid cookie; cleanup UNKNOWN | Down |
| Replace old authority file with new display's authority | Owner base reused by supervisor; release readback verified, overall cleanup UNKNOWN | Up; fresh target observed `b` release |

Both displays were `:0`. In each arm the fresh guarded task subsequently
delivered `a` to its target and verified its release. The old target exited with
code 1 because its X server was deliberately retired; the fresh target exited 0.
The supervisor's `release_confirmed` stayed false and replay was disallowed.

This is a concrete counterexample to treating a mutable authority **path** plus
an X resource base as a sufficient display-generation fence: under this injected
replacement, stale cleanup reached and changed a fresh generation. It does not
establish that normal code replaces the authority file, that a real cancellation
necessarily creates the synthetic obligation, or that the production runtime is
integrated with display retirement. Keep the display owner experimental until
the cleanup path is bound to the correct display generation and tested across
retirement and replacement. A same-name display and matching X resource base are
not proof of the same server.

`raw.zip` contains conditions, launcher outputs, results, target events, and
guarded artifacts. `manifest.json` freezes the full candidate source and trial
inputs; the code snapshot is based on main `e5925b6` plus the draft's explicit
authority changes at `926ba07`. The pinned image, CPU/memory/network limits,
and one attempt per arm are in the conditions and launcher. Authority files
and private command paths are excluded; all four local authority records were
scanned against every included file for raw and hex-encoded cookies. This is one
ordered pair, not a rate or latency estimate.
