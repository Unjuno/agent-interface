# Issue #6744 — OrbStack namespace-safe reproduction A02

**Allocation:** `6003-container-repro-a02-20261003`
**Status:** candidate and independent audit each executed once in separate OrbStack containers.
**Disposition:** `PASS_CONTAINER_REPRODUCTION_SCOPED`.
**Integration branch:** `research/6003-container-repro-a01-20261003`.
**Frozen base:** `e52c4a65915cf48641c63cc95950be15f1b77cbf` (preservation-only PRs #6742/#6743 and adjacent #6616 documentation changes).
**Integration rebase:** after candidate/auditor completion, the branch was fast-forwarded to main `162963a9aed79e7a9ca233e9218c02c1608b0ab7` (preservation-only PR #6741); frozen inputs and raw results were unchanged.

This distinct allocation follows #6740 A01's terminal `FAIL_RUNNER_IMPORT_COLLISION_NO_METHOD_RESULT`. The A01 result remains unchanged. A02 changes only the Python invocation context; FREEZE.json, selector, and independent auditor are byte-identical to A01. It will test only whether safe import resolution allows the finite selector result to be reproduced.

## H / T / D / C / U

- **H:** A namespace-safe Python entrypoint, executed from `/` with `sys.path[0]="/"`, avoids local `select.py` shadowing and reproduces the predecessor's A/B selector choices and controls.
- **T:** One candidate and one independent mathematical auditor in separate containers from the pinned, already-local OrbStack Python image. Use network none, read-only root and mounts, one CPU, 256 MiB, 64 PIDs, dropped capabilities, no-new-privileges, non-root UID, and 16 MiB tmpfs. Print and hash complete result JSON to container stdout before exit. Exact commands are in [RUNBOOK.md](RUNBOOK.md).
- **D:** `PASS_CONTAINER_REPRODUCTION_SCOPED` only if both invocations exit 0, audit errors are empty, cheapest/nominal entropy choose A, robust reversal chooses B, prior-rank reversal holds, null is UNRANKABLE, hard sentinel remains, STOP contributes no support, and outputs match the retained host result. Any failed invocation is terminal for A02.
- **C:** One authored finite table, one OrbStack arm64 host, one pinned local Python image, one candidate/auditor pair.
- **U:** Synthetic method reproducibility only; no calibrated priors, real research-productivity, GUI/runtime, safety-effectiveness, or broad-portability claim.

The source hashes and metadata-only deltas from the host predecessor are retained in [the A01 package](../decision_reversal_6003_container_repro_a01_20261003/SOURCE_DIFF.md). A01's failure trace is not pooled as selector evidence.

## Result

The namespace-safe entrypoint completed the unchanged selector source in Python 3.12.14 without the A01 import collision. The separate independent mathematical auditor exited 0 with `errors=[]`. Candidate and auditor raw stdout were retained; printed file SHA-256 values match the extracted JSON bytes.

- Cheapest-first: `A-cheap-irrelevant`.
- Nominal entropy: `A-cheap-irrelevant` (2 bits).
- Robust worst-case decision reversal: `B-robust-reversal` (min scenario mass 0.60; A=0, C=0.10).
- Null control: `UNRANKABLE` with all reversal scores 0.
- Prior-sensitivity control: nominal entropy C>B; capture-lean entropy B>C.
- Hard sentinel remains mandatory; STOP is excluded from reversal/support; scientific support events=0.
- The parsed `primary` and `null_control` objects exactly match the retained host predecessor.
- Candidate JSON SHA-256: `a3244442a2707424d2a97d024bc3061a2f9ab2a6ddcf3f76f6cfc3d731477c74`.
- Independent audit JSON SHA-256: `acee0a4c27ecc37bf0e3e424fa43223e15628955a6848a224d4531a6686a2fb8`.
- Candidate/auditor container IDs, image digest, engine, isolation settings, output hashes, and parity details are retained in `execution/`.

This is a scoped reproduction of an authored finite selector. It does not show that the selected experiment would improve actual research allocation or roadmap outcomes; the illustrative priors and consequences remain authored.

## Local integration gate

The local equivalent of the branch's `.github/workflows/analysis-index.yml` command set passed using Python 3.12.13: analysis-index plus 19 test steps, 114 tests total. This included both A01/A02 construction suites and the workflow's unrelated retained analytical checks. An initial run exposed the intentionally sparse task checkout missing the workflow file read by one #6590 test; the worktree was expanded, the workflow's pinned source was restored and hash-checked, the failed gate passed, and then the complete command set passed. The branch workflow file was restored to its committed version afterward. Details: `execution/LOCAL_CI.json`.
