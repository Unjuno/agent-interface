# Immediate-modal baseline T0 — Issue #6492

Disposition: `STOP_INFRASTRUCTURE_BEFORE_CONTAINER`. The single frozen Docker
launch attempt exited 127 before a container was created because Docker CLI
could not create its host-side `--cidfile` at `/out/container.id`. Candidate
Python invocations=0; independent auditor=0; retries=0. Exact command, stdout,
stderr, exit code and hashes are retained in `RUN.json` and `results/candidate/`.
Under the no-retry gate, this allocation is terminal; no same-allocation
relaunch was attempted.

The proposed method tests only six `immediate_modal` records missing from PR
#6499's timing-only/preserved-view/optional-cue assay. No candidate output was
produced, so there is no method PASS/FAIL/HOLD and no result about the
immediate-modal contract. No participant, GUI, model, real interrupt, private
content or effect was involved. No human-benefit or product conclusion follows.
