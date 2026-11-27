# R36 — strict public-cancel release gate

This packet tests the original 1250 ms post-cancel gate after correcting R35’s pre-cancel `hold_ms` local-variable ordering. Conditions are frozen before one live trial. A public cancel attempt is timestamped before its call and persisted even on error. The hook’s absolute self-deadline is finite; after cancel response the caller polls the exact call ID for the full 1250 ms, with at least 21 polls required for a strict pass.

The pre-armed same-generation sampler is shut down before `interface_close` so fixture retirement cannot turn an otherwise valid series into a stale-generation error. A single attempt only; no retry or replay. See `RESULT.md` and `audit_r36.json` after the trial.
