# #5184 fresh-seed typed-mode successor

## Current status

Allocation -03 (`typed-mode-4844-successor-20260928-03`) completed one runner and one independent auditor under Docker Desktop. The preregistered result is **`HOLD_COVERAGE_TRADEOFF`**. This is finite synthetic evidence only; it does not support deployment or real-application claims. Allocation -02 remains a pre-container STOP and was not retried; seeds 484421/484422 were not reused.

After completion, publication collided with a concurrently created Issue #5189 branch that had frozen the same allocation ID, original path, and seeds under a different source implementation. Our source commit is dated 13:16:53+09:00 and runner started 13:18:08+09:00; the peer freeze commit is dated 13:22:33+09:00 and its runner started 13:24:56+09:00. The peer reconciliation merged in PR #5191 classifies its later run as `STOP_DUPLICATE_FORMAL_SEED_COLLISION`; our #5184 run remains the first completed formal execution. We did not overwrite the peer branch. Its raw (`74dfede0…`) is preserved separately and must not be pooled or averaged with this result. This result is retained under the unique collision-safe delivery path; exact chronology/source paths and both raw hashes are recorded in `RUN_RECORD.json`, `PARALLEL_COLLISION.md`, and Git history.

### Preserved predecessor failures

- #4844 allocation `typed-mode-4844-seed-484401-v1`: `STOP_PROVENANCE_OR_AUDIT`; its 3,000-row metrics remain exploratory and do not adjudicate the hypothesis.
- A conflicting #4844 comment reports a 4,800-row `FAIL_MODE_MISROUTES_RECOVERY`, but links to #4155's different evidence path and seed family. It is not pooled or used as a formal result here.
- Successor allocation -01: `STOP_PREFORMAL_SEED_EXPOSURE`. A Stage-0 test accidentally ran the full generator with candidate seeds 484411/484412 before freeze. It did not run in Docker, persist raw output, or produce a retained numerical estimate. Those seeds are retired, recorded in Issue #5184, and are not reused.
- Successor allocation -02: `STOP_DOCKER_IMAGE_ARGUMENT_MISMATCH`. Docker returned exit 125 before container creation because the CLI image argument omitted `681`. No seeds were accessed and no raw result exists; the evidence is preserved in the sibling v2 bundle and PR #5188. Seeds 484421/484422 are retired.

## H / T / D / C / U

See [PLAN.md](PLAN.md) for the complete frozen hypothesis, exact schedules, decision gates, confounders, and scope limits. Current Stage-0 uses only seeds 17003/17004, disjoint from all formal allocations.

## Stage-0 result

On Windows 11 / CPython 3.12.10, `python -B -m unittest -v test_stage0.py` passed **9/9**. It verifies the 4,800-row accounting on construction-only seeds, 960 rows per block and 192 per mode, full-observation and unknown controls, 16 evidence mutation rejections, canonical raw serialization, duplicate-key rejection, frozen source digests/sidecar, disjoint formal/construction seeds, that Docker image arguments are sourced from the frozen JSON rather than manually transcribed, and that a valid but failed control is reported as a scientific failure rather than an audit STOP. This is construction evidence only.

Docker Desktop `desktop-linux` reports Engine 28.5.1 linux/x86_64 and an empty running inventory. The selected cached pinned image `sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a` was launched once in a bounded no-network/read-only smoke check and reported CPython 3.12.14; the container exited and the inventory returned empty. This is environment readiness, not the formal experiment.

## Formal result — allocation -03

Frozen source commit `2a96313df5edffb1f7d180bee6c142917ac79e37`; current-main intake `dbfae29cf848e4beee8f0287a9843532f5a695a8`; train/heldout seeds 484431/484432. Docker Desktop `desktop-linux`, Engine 28.5.1, pinned image from `FREEZE.json`, `linux/amd64`, no network, read-only root/source, 1 CPU, 512 MiB, 32 PIDs. Runner and independent raw-only auditor each ran once, exited 0, and left no running containers. Auditor accepted the canonical 4,800-row raw (`51d9c7fed88a5a491a7e1f4fb5a33349ffe58c486a44a946b573a1a18838e300`), reported zero audit errors, and rejected all 16 mutation controls.

| Block | Direct wrong / coverage | Typed wrong / coverage | Relative wrong reduction | Coverage loss | Gate |
|---|---:|---:|---:|---:|---|
| COMPLETE | 74 / 94.79% | 36 / 95.00% | 51.35% | -0.21 pp | descriptive |
| SINGLE_MISSING | 49 / 30.00% | 61 / 77.50% | -24.49% | -47.50 pp | fail |
| MULTI_MISSING | 37 / 28.13% | 79 / 70.21% | -113.51% | -42.08 pp | fail |
| COMPOSITION_HOLDOUT | 217 / 74.17% | 149 / 59.06% | 31.34% | 15.10 pp | fail: >5 pp tradeoff |
| NUISANCE_SHIFT | 131 / 67.40% | 125 / 68.44% | 4.58% | -1.04 pp | descriptive |

All unsafe-emission counts were zero. The five noiseless full-observation controls matched the correct truth in both arms; unknown and contradictory controls abstained in both arms. The composition block clears the error-reduction threshold but misses the registered coverage-loss bound by about 10.10 percentage points; the other two primary blocks increase wrong emissions. The preregistered disposition is therefore `HOLD_COVERAGE_TRADEOFF`, not PASS. These are descriptive outcomes from one synthetic seed pair, without population-level inference.

The raw output, runner/auditor stdout and stderr, container IDs and compact receipts, and independent audit result are preserved under `formal/allocation-03/`.

## Frozen source and evidence boundary

`FREEZE.json` binds each runner/auditor/test source by Git blob, SHA-256, and byte count; `FREEZE.sha256` binds the freeze document. Allocation -03 obeyed the one-runner/one-auditor/no-retry boundary. The exact raw bytes and receipts are preserved; no formal output was modified after audit.
