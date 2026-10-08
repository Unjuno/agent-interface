# Issue #5970 T1 — retained reconnect-trace applicability audit

## H / T / D / C / U

- **H:** The retained X11 reconnect positive traces contain enough source-bound causal-parent or send/receive evidence to reconstruct a nontrivial causal cut between the fresh key-state bootstrap, observer events, and independently observed Tk application state.
- **T1:** On frozen main, verify the complete retained reconnect evidence archive and its published source hashes; inspect all four `REBOOTSTRAP_ON_RECONNECT` rows for `DISCONNECT_PRESS` and `DISCONNECT_RELEASE` across both repetitions. Compare embedded raw observer/app event files to aggregated case rows; verify bootstrap epoch binding; inventory explicit causal-edge fields. No X11/game/model/input/runtime execution.
- **D:** `PASS_TRACE_CUT_APPLICABILITY` only if all four rows have complete raw/aggregate agreement, correctly bound bootstrap epochs, and explicit cross-source causal edges sufficient for a nontrivial cut. `HOLD_CAUSAL_EDGE_PROVENANCE_MISSING` if the relevant reconnect state exists but explicit cross-source edges are absent. `HOLD_NO_ELIGIBLE_TRACE` only if no relevant reconnect/bootstrap state exists. Integrity failure is STOP, not a scientific disposition.
- **C:** Same-host monotonic timestamps can help order events but do not alone encode send/receive or causal-parent edges. A single observer connection may provide an atomic root and event stream; that does not establish coherence with separately recorded application state.
- **U:** This audit covers one archived Xvfb/Tk fixture and four positive-policy rows. It does not prove real-world causal consistency, semantic truth, authorization, task benefit, or the frequency of cross-source recovery bundles.

The audit is read-only over a frozen repository archive. It uses host Python in memory because Docker Desktop is unavailable; no container, runtime, GUI, model, or input was started.
