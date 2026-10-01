# Identity resolver result (#2664)

Local Docker allocation, pinned `python:3.12-slim-bookworm`, private Xvfb
`:142`, and `0600` Xauthority:

```json
{"decision":"FAIL_WINDOW_IDENTITY_RESOLVER",
 "apps":{
   "inkscape":{"candidate_count":0,"disposition":"refused_ambiguous_or_missing"},
   "calc":{"candidate_count":0,"disposition":"refused_ambiguous_or_missing"},
   "chromium":{"candidate_count":1,"disposition":"accepted"}},
 "controls":[{"control":"missing_token","candidate_count":0,"disposition":"refused"}],
 "input_operations":0,"model_calls":0,"network_calls":0}
```

This successor did not run the #2499 transition sequence or any task input.
The resolver correctly failed closed for the two missing identities, but the
hypothesis was not met because all three applications did not bind uniquely.
