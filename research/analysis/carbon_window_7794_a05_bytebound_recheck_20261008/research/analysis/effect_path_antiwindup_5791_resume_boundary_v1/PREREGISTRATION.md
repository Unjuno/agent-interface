# Issue #5791 persistent-runner boundary construction — preregistration

## H/T/D/C/U

- **H:** Given the frozen `map01_persistent_model_runner_v2.py`, an offline CLI stub will observe exactly one initial `codex exec` request with the supplied first prompt, then exactly one `codex exec resume` request carrying the thread ID reported by the first response and the supplied second prompt (including the explicit no-visible-effect action feedback). This tests runner boundary wiring, not whether the provider semantically retains earlier intent.
- **T:** Invoke the frozen runner twice through its real subprocess path, replacing only Node/Codex CLI with a local fake executable implemented in Python. First response emits one `thread.started` ID; the harness reads that ID from runner output and supplies it as the resume session. Candidate exactly once; independent raw-only auditor exactly once after candidate exit 0.
- **D:** `PASS_STUBBED_RUNNER_RESUME_AND_PROMPT_FORWARDING` iff there are exactly two stub invocations; argv are initial `exec` then `exec resume <same returned thread ID>`; each stdin matches its frozen prompt byte-for-byte; the second prompt contains the explicit prior no-visible-effect action; both runner event plans identify correct mode/session and exit 0. Any violation is retained FAIL/STOP without retry.
- **C:** Windows host, CPython 3.11.9, local subprocess and filesystem behavior; fake CLI supplies deterministic JSONL and does not access a model or network.
- **U:** Does not test the real Codex CLI, provider transcript retention, model reasoning/behavior, gameplay, live GUI, GPU, task effect, or hidden accumulation. No conclusion about latent model-session state is permitted.

## Frozen identity

- Repository `Unjuno/agent-interface`, main `bd9c4c5ceca68f4dc09bb39d27b140a987b68656`.
- Source `research/doom/map01_persistent_model_runner_v2.py`, Git blob `a6f51c7e92f06213c97978889bb029ac1b581dfc`.
- Local executable fixture is `runner_v2.py`, exact source after CRLF→LF normalization; all executable fixture SHA-256 values are listed in `FREEZE.json`.
- Candidate command: `python -B candidate.py`.
- Audit command (only after candidate exit 0): `python -B audit.py`.
- No Docker daemon was used: a separate task has an exclusive Docker Desktop allocation beginning 06:21 UTC, and the most recent independent probe documented a connected but unresponsive Docker Engine. This bounded local process-boundary test uses only CPU/filesystem and does not touch that allocation.
- No model, provider, network, GPU, game, GUI, input, or external workflow.

## Frozen scenario

The initial prompt carries an empty effect-history list. The stub returns `fixture-thread-5791`. The resume prompt carries `Previous no-visible-effect actions: ["forward"]`. The only manipulated factor is initial versus resumed runner invocation; model/model-provider behavior is outside the candidate.

## Pre-candidate freeze STOP

The first local freeze-integrity check failed before any candidate or stub invocation because the Python executable SHA-256 was transcribed incorrectly in `FREEZE.json`. All fixture-file hashes checked before that gate matched. The incorrect digest was replaced with the observed hash `5f7b89a612c9b8af1d6456cdfcd1dbe5ca630849e79aebced9bee9a6694952ec`; candidate count remained zero. The corrected freeze is subject to one fresh integrity check before candidate start.
