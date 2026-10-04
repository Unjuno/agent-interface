# A02 first result — STOP

The A02 candidate ran exactly once in the fresh isolated guest. It launched Xvfb, created the test client, then stopped during client-focus setup. Python-Xlib 0.33 expected `Display.set_input_focus(focus, revert_to, time)`; the frozen candidate supplied `(revert_to, focus, time)`. The resulting `ValueError` occurred before InputOwner construction and before any input event.

The candidate returned 2 and wrote the raw first outcome. The independent raw-only auditor ran once and returned `FAIL` because the trace contains no action/admission/event rows. Per the preregistered rule, this incomplete setup is classified `STOP`, not a completed measurement mismatch. Xvfb was stopped with exit 0. No candidate rerun is allowed.

The correction is limited to argument order and must be tested under a new allocation identity. This does not test a game, model, task effect, threat exposure, recovery, or MAP01 progress.
