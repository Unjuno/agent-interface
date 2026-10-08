# Issue #5791 persistent-runner resume boundary construction

## Result

**PASS_STUBBED_RUNNER_RESUME_AND_PROMPT_FORWARDING** for the exact v2 runner wrapper. The independent auditor verified one initial invocation, then one exec resume invocation using the session ID returned by the first response. The second prompt reached the stub byte-for-byte and included the explicit previous no-visible-effect action feedback.

This is only runner wiring. It does not test the real Codex CLI/provider transcript or prove that a model retains, forgets, or accumulates correction intent. Accordingly, external-context anti-windup eligibility remains **HOLD / UNTESTED**, not eligible or ineligible.

## Experiment

H/T/D/C/U and the frozen decision gates are in [PREREGISTRATION.md](PREREGISTRATION.md); source and executable SHA-256 values are in [FREEZE.json](FREEZE.json). Candidate ran once using:

    python -B candidate.py

It launched the frozen runner twice through local subprocesses, with only the CLI executable replaced by a deterministic Python stub. The initial stub returned fixture-thread-5791; candidate then passed that identifier into the real runner's resume branch. The two raw invocations, prompt bytes, runner event streams, plans, process receipts, and captured command output are retained under [candidate-output/](candidate-output/).

The separate raw-only auditor ran once:

    python -B audit.py

It exited 0 and produced [audit.stdout.json](audit.stdout.json). Candidate and auditor both used CPython 3.11.9 on Windows 10.0.26200; no container was used. Docker Desktop had a separately reserved 06:21–06:24 UTC window and recent engine-unresponsive diagnostics. This experiment needed only local CPU and process I/O, so it did not touch the daemon.

## Preserved preflight STOP

An earlier freeze-integrity check stopped before candidate execution because the Python executable SHA-256 had been transcribed incorrectly. All fixture hashes checked before that point matched. The incorrect digest was corrected, the STOP recorded in the preregistration, and the corrected integrity check passed before the sole candidate run. No candidate rerun occurred.

## Scope and next gate

The source runner selects exec resume, passes the returned thread ID, and feeds the next per-turn prompt. That establishes an external session continuation request plus explicit feedback forwarding. The provider's stored transcript and semantic effect are opaque here. Do not implement anti-windup or claim hidden-state behavior from this construction. A future test of the actual Codex CLI/provider boundary would require an explicitly authorized model allocation with retained, inspectable transcript evidence; absent that, keep this boundary unverified and the issue open.
