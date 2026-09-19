# Result: FAIL_XAUTH_COOKIE_IDENTITY

One local Docker allocation used private Xvfb `:143`, a generated
MIT-MAGIC-COOKIE, and `0600` Xauthority. Chromium produced one matching xprop
candidate; Inkscape and Calc produced zero and were refused closed. The missing
control also refused. Xauthority SHA-256 was
`d9dfb9e99add037e4a6ac43c43df2f6ee067dca86c0560d6003b790f6b12ee8f`.

`input_operations=0`, `model_calls=0`, and `network_calls=0`. Decision:
`FAIL_XAUTH_COOKIE_IDENTITY`. The cookie construction did not resolve the
identity gap; no #2499 transition or task input was attempted.
