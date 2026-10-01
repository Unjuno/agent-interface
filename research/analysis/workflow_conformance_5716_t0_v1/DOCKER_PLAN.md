# Issue 5716 isolated Docker construction plan

Allocation: `5716-TELEMETRY-IDENTIFIABILITY-DOCKER-CONSTRUCTION-20261001-01`

## H / T / D / C / U

- **H:** The telemetry-only checker cannot distinguish the preregistered release-gap worlds from identical visible input. Unknown release-channel completeness must yield `UNKNOWN_TELEMETRY` in both worlds.
- **T:** One GitHub-hosted Linux runner, triggered only by creation of the frozen allocation branch. It starts one candidate container and, only after candidate exit 0, one separate raw-only auditor container. Both use the same exact platform-specific selection from a digest-pinned official Python image with `--network none`, read-only root filesystem, bounded memory/CPU/PIDs, and read-only source/input mounts. The candidate consumes the four frozen rows; the raw auditor validates the exact retained stdout SHA and all four exact rows. One run attempt only; no retry.
- **D:** PASS only if start-gate/source/image identities pass, candidate exits 0 and emits exactly 665 bytes with SHA-256 `89a64b887353d6448acdd09fcd6719613fbf1abee7cdf6f44b4d0b5a26f72ed9`, and the separate auditor exits 0 with `PASS_IDENTIFIABILITY_CONSTRUCTION`. Any start/image/source/runtime ambiguity is STOP, not scientific FAIL. Candidate/auditor invocation counts and actual Docker inspect receipts must be retained.
- **C:** Synthetic event data only; Docker image `python:3.12.14-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, requested platform `linux/amd64`, network disabled inside both containers. The hosted runner is an isolated fallback because this Windows Docker Desktop engine is stopped; it is not evidence from the local Desktop engine.
- **U:** Confirms only reproducibility of this finite identifiability construction in the pinned container. No live telemetry loss, external effect, workflow-wide conformance, task correctness, safety, runtime, or product claim.

Source, fixture, auditor, workflow, image and allocation identities are in `DOCKER_FREEZE.json`. Results will be retained under `results/identifiability-docker-construction-01/`.

