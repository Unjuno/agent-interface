# Caller-owned public dispatch: primary Calc use

Actual source: 417254c48 (full revision in Git history); fresh Calc seed 991293.
The primary used one managed MCP SDK client, personally reviewed the initial
image and both action images, entered 598 and 701, saved, confirmed the format
dialog, then finished. There were two input programs, no input replay, extra
observation or helper model. Global text gap was 2 ms; both actions retained
250 ms post-action waits.

Both native guarded programs passed through public dispatch_in_session and
retained the public result envelope: returned/completed, with empty and verified
input-release records. Saved XLSX independently reads A1=598 and A2=701.
Finish evaluation succeeded; native_status recorded owner PID 64708 exit 0.
The managed client exited 0 (terminal observation, not inferred by verify.py).
Descendant cleanup is not claimed.

This integrates compilation/dispatch reporting with the native caller-owned
session. Contract tests verify no backend opening/closing, no retry on failure,
and preservation of recovery refusal. The live archive does not independently
measure connection identity. Public MCP remains one-shot; a shared persistent
transport lifecycle, model-token measurement and overall integration acceptance
remain open. No latency, human-tempo or token improvement is claimed.

Run python3 verify.py here for retained hashes, saved cells, both public result
envelopes/input releases and owner exit. This does not replay UI actions.
