# V39 active observation queue composition A04

Disposition before candidate: `PREREGISTERED_NOT_RUN`. Parent: Issue [#59](https://github.com/Unjuno/agent-interface/issues/59).

## H / T / D / C / U

- **H:** When two differently tagged, image-paired `toolOutput` observations are acknowledged on one active Codex App Server turn while its initial Responses request is still pending, the next serialized model request(s) either preserve both in sequence, retain only one, reverse/interleave them, or reject a message. This tests whether a fresh soft observation can replace an older queued prefix while inference is pending.
- **T:** On current main `2f2c83c3da36566bac410b13b2ed5202c9641f1a`, run the frozen Windows Codex CLI 0.160.0 App Server probe once against a loopback-only Responses mock. Hold every mock response. Start one turn, send observation 201 and then 202 as separate `turn/start.toolOutput` RPCs, verify each returned the same in-progress turn ID, wait the frozen 2.0-second pending window, then release mock responses in request order. Retain exact request JSON, RPC replies, timestamps, and outputs. No retry or negative-control run.
- **D:** Classify successful complete observations as `BOTH_IN_ONE_FOLLOWUP_ORDERED`, `BOTH_ACROSS_FOLLOWUPS_ORDERED`, `LATEST_ONLY`, `FIRST_ONLY`, `BOTH_REVERSED`, `BOTH_UNORDERED`, or `NEITHER_OBSERVED`. A structured error reply for either observation RPC is `RPC_REJECTED`; a missing or malformed RPC reply is unverifiable. Only matched text+exact-image pairs count as delivered. Missing/mismatched turn identity, split text/image, missing terminal notification, mock errors, or incomplete raw data is `PARTIAL_OR_UNVERIFIABLE`/`UNVERIFIABLE`; retain it without retry. One observation is not a reliability estimate.
- **C:** The result is specific to this Codex CLI/App Server version and local mock scheduling. Holding all mock replies prevents a generated mock response from racing the second observation, but is not a live provider/model latency distribution. A request serializer may preserve order without the model understanding or acting on the images.
- **U:** Synthetic one-pixel images verify byte identity only. No model inference, game, GUI, OS input, action cancellation/release, task feedback, recovery, latency benefit, or MAP01 outcome is measured. This cannot satisfy Issue #59's live threat-exposure gate; the private live lane remains unassigned.

## Distinction from existing results

PR #7951 tests one `turn/externalMessage` observation and its text/image serialization. PR #7969 tests the timing/order of one `toolOutput` observation relative to one pending request. PR #7987 tests one legacy `turn/steer` observation on CLI 0.146.1. This A04 asks whether *two* distinct current-version `toolOutput` observations received before the first response are both retained, coalesced, or split across follow-up requests. It does not rerun those single-message questions.

## Freeze and isolation

Exact source identities, executable hash, fixtures, command, timeouts, and labels are frozen in `FROZEN.json`. Both 1x1 PNGs are generated deterministically by `make_frames.py` and sent only to the local mock. The candidate uses a fresh temporary `CODEX_HOME`, removes API-key/base-URL/organization/project and proxy variables from the child, sets the model provider endpoint to `127.0.0.1`, and requests no external model service. The App Server runs read-only with approvals disabled. The formal candidate uses no game, GUI, input backend, GPU, or user file; only the documented WSLc compatibility preflight starts a disposable container.

### Runtime selection

Repository `docs/CURRENT_GOAL.md` requires WSLc for eligible local single-container CPU work. WSLc 3.0.1.0 was available; before testing, its container list was empty and the `python:3.12-slim` image was already present. A single network-disabled, 0.5-CPU, `--pull never`, read-only-mount construction probe attempted only `codex.exe --version` inside that Linux image. It exited 255 with `exec /opt/codex.exe: exec format error`; the post-probe container list was empty. This establishes that this installed Windows Codex executable cannot run in the selected Linux container image. The measurement specifically targets the native Windows Codex App Server process and its temporary Windows `CODEX_HOME` plus same-host loopback transport, so placing only the mock in WSLc while leaving the subject process on Windows would split the frozen environment and change the transport boundary. The one-shot protocol candidate therefore uses the isolated native-Windows host process; no game/live lane is involved. Preflight command, raw output and exit receipt are retained under `environment/`.

Candidate stdout/stderr, exit code, command, independent audit, and checksums belong in `results/`. A passing construction suite or a retained protocol result is not evidence of model comprehension or useful control behavior.
