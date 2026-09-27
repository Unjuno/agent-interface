# Construction pilot 02 — STOP

The receiver-only diagnostic succeeded in all four fresh Xvfb cases: the mapped InputOnly window's XID matched `GetInputFocus`, and the receiver logged exactly `a` KeyPress/KeyRelease. The harness then stopped at the layout-evidence gate because its `xkbcomp` argv was incorrect and produced an empty dump. It did not reach unsupported-input or candidate-delivery checks. Raw partial output and logs are retained unchanged. This is a construction STOP, not a runtime/candidate failure.
