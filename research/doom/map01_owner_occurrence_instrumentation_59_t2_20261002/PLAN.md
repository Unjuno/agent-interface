# #59 isolated InputOwner occurrence-instrumentation construction T2

## H / T / D / C / U

- **H:** The pinned owner can be minimally instrumented to return a unique interval ID at each down and carry the same ID through its matching explicit up, without changing the ordered key events.
- **T:** First run a RED behavioral test against the unchanged pinned source. Then add only an isolated copy/prototype patch, run the same construction test GREEN, add a second test requiring pre-down/post-down/post-up keymap witness receipts, and run it RED then GREEN. After freezing the patched copy/harness/cases, run one candidate plus one independent raw-only audit. Construction red/green invocations are not the frozen candidate allocation; no live/X11 call.
- **D:** Prototype passes only when two distinct IDs bind one-to-one across admissions/releases, each interval has 32-byte pre-down, post-down, and post-up keymap receipts carrying that ID, fake event order stays press/release/press/release, and terminal state is empty. Auditor mismatch is FAIL.
- **C:** Current main anchor `3adec9cdc2cff5ef68f19acd55c5823fcaad26df`; CURRENT_GOAL blob `dd6d691331bd602f97d9aa0e3f52fc6202b06525`; ROADMAP blob `c322beb5fc2a9f6217dd3cc6205b9cbf05e84c19`. Owner dependency pinned to #5630 commit `288d0498d11cf16657e523a04616bf4f49cd94f4`, blob `c40db07e596b31557590cec5e90f6ab651573476`. Current r133 path needs actual held-input occupancy; #5085 has no live Docker allocation, so construction only.
- **U:** The fork is an instrumentation prototype under an in-process fake Xlib transport, not production code or real physical occupancy. No Docker, X server, keyboard, game, model, GUI, application effect, latency, safety, or MAP01 claim. It does not authorize or spend the live allocation.

## Frozen boundaries

All modifications stay in this path. The pinned dependency and earlier T0/T1 reports are immutable. A construction failure stays in the run record; only the final prospectively frozen candidate/audit pair is reported as the formal construction outcome.
