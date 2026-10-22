# Matched private-Xvfb service pause pilot

**Run ID:** `AI-XVFB-PAUSED-SERVER-MATCHED-PILOT-20261022-01`
**Frozen baseline:** current main `cc5ef16c560cc985ee0951d3d53d659e892f5167`
**Environment:** Ubuntu 24.04 WSL2, CPython 3.12.3, private user/mount namespace, fresh Xvfb `:88` per trial.

## Question

Across three ordered pairs, does a 1.5 s pause of the entire private Xvfb process change admission-to-response timing, post-resume input release, or fresh-session task verification relative to the same standard-caller schedule with no pause?

## Frozen design

Six independent candidate invocations, each on a fresh Xvfb process and unique output folder; never retry an invocation. Same current-main source, cached dependencies, one-second owner-ack withholding, eight-second delayed request, 45 s hard timeout, and caller admission deadline in all trials. Pair order is fixed before execution: pair 1 `C01` then `P01`; pair 2 `P02` then `C02`; pair 3 `C03` then `P03`. C trials have no server pause; P trials SIGSTOP only their exact `/usr/bin/Xvfb :88` PID for an automatically resumed 1,500 ms. The test validates PID executable and display before signaling. A private mode-1777 tmpfs socket directory isolates each trial.

Primary per-trial composite: caller returns within 300 ms of cancellation admission; response preserves pending/UNKNOWN/no-replay; cancellation terminates within 5 s; release readback and independent all-up readback succeed; delayed-request horizon has no old press; distinct fresh target/session/process generation passes the independent synthetic task oracle; old cancellation remains UNKNOWN. For P trials, caller must return while Xvfb remains stopped, and release must occur after resume. Compare per-arm success counts and timing distributions descriptively; n=3 per arm is a pilot, not broad reliability evidence.

## Stop and preservation rules

Preflight source/dependency/namespace/display checks must all pass before trial 1. Preserve every test and Xvfb exit code, output, result JSON, process identity, and hash. Continue through the predeclared sequence after a candidate failure, but never retry a failed or incomplete trial. No package installation, download, WSLc, Docker, or container/image operation.
