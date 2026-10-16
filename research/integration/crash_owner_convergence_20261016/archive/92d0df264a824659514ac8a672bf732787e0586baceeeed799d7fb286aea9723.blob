# A03 — setup STOP: pre-existing output directory

**Disposition: `STOP_INFRA_OUTPUT_PATH_PREEXISTED`.** The one candidate invocation failed at its initial `OUT.mkdir(exist_ok=False)` because the result directory had been created while preparing the run. Xvfb and the session child never started. No candidate raw file exists; `RUN.json` preserves the observed command and failure, and `AUDIT.json` verifies the frozen source hashes and limited disposition.

A03 is not a backend result and is not retried. The A04 successor uses a distinct, absent output leaf and does not pre-create it; all input/Xvfb gates remain frozen.
