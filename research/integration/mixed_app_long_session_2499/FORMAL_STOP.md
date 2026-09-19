# Formal mixed-app session result: STOP

Successor Issue: #2499

The single frozen local Docker allocation was started with a private Xvfb
display `:141`, `0600` Xauthority, and the pinned `python:3.12-slim-bookworm`
container plus Inkscape, LibreOffice Calc, Chromium, and xdotool. It stopped at
the first window-identity acquisition before any transition or task input:

```json
{"decision":"STOP_MIXED_APP_LONG_SESSION",
 "error":"TypeError('expected str, bytes or os.PathLike object, not NoneType')",
 "ledger":[
   {"kind":"session_setup","display":":141","xauthority_mode":"0600"},
   {"kind":"stop","reason":"window identity was None"}
 ],"model_calls":0,"network_calls":0}
```

This is a retained formal STOP, not a PASS/HOLD substitution and not a reason
to relabel the earlier construction gate. The preregistered one-allocation
rule means the session is not rerun or tuned in this result path. The next
successor must repair per-window identity discovery in a new preregistered
allocation before claiming any integrated trace.
