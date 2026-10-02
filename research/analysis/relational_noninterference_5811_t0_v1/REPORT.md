# Issue #5811 — relational non-interference T0 report

## Result

**PASS_METHOD_SCOPED**, limited to the frozen deterministic synthetic fixture. GitHub Actions run [36825844461](https://github.com/Unjuno/agent-interface/actions/runs/36825844461) executed the candidate once and the independent auditor once, both with exit code 0. The auditor reconstructed all 10 cases and accepted five mutation controls.

| Outcome | Cases |
|---|---:|
| `RELATION_HOLDS_SCOPED` | 1 |
| `CONFIRMED_CROSS_SESSION_EFFECT` | 2 |
| `NOT_INDEPENDENT` | 1 |
| `UNKNOWN_COVERAGE` | 6 |

The confirmed cases are `delayed_receipt_to_A` and `B_cleanup_releases_A_input`. Both standalone histories report DONE/saved/EMPTY and have equal final state, while A's paired relational projection contains a B-produced receipt or cleanup/release targeting A. The clean disjoint control holds. The shared verifier-capacity control is `SHARED_BY_CONTRACT` / `NOT_INDEPENDENT`; its explicitly allowed queue-use rows remain in the footprint audit but are excluded from semantic projection equality.

The other six cases remain UNKNOWN, not successful independence evidence. In particular, the misbound-observation fixture exposes a foreign event but its dependency coverage is incomplete, so the preregistered rule does not promote that event to a scored independent-session result. Hidden global focus and the shared document likewise do not establish complete independent footprints.

## Execution evidence

The allocation is `5811-RELATIONAL-NONINTERFERENCE-T0-20261001-01`, run number 1, attempt 1, frozen event SHA `367833ea2d648cf339ff9fa9cc75cd6340ac779a`. The start gate passed at main `472bedbe5a44a4247c8bd63ff584a4f15b78b8ab`. Runner Docker Engine was 28.0.4. Both separate linux/amd64 containers used `python:3.12.14-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, network none, read-only root, 128 MiB, CPU 1, pids 32, cap-drop ALL; both exited 0 with OOM false. The raw JSON SHA256 is `f9c64ad515b84c22c8bd5b9bc9f3bfe82eee5c6718288c25ac27abdd516495c3`, matching `SHA256SUMS`.

Machine-readable candidate output, independent audit, runner/container inspection, image identity, start-gate record and checksum are retained under `results/5811-RELATIONAL-NONINTERFERENCE-T0-20261001-01/`.

## Limits and next step

This does not demonstrate live GUI isolation, complete real-world instrumentation, production safety, throughput, or a general non-interference theorem. The six UNKNOWN histories identify where the current finite evidence contract cannot defend independence; a successor may add source-bound global-focus and shared-document event inventories and repair the misbound-observation coverage, while preserving this allocation unchanged. Any live two-client study still requires a separate preregistration, disposable environment and independent effect oracle; do not infer it from this synthetic result.
