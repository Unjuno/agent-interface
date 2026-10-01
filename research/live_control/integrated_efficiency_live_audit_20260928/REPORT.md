# Integrated live allocation evidence audit — 2026-09-28

## H / T / D / C / U

- **H:** The retained `integrated-efficiency-live-01` task trace, raw call result files, exact submission histories and published arm totals are internally reconstructable without using its existing audit/evaluation code.
- **T:** An independent filesystem-level recount of immutable evidence from source commit `9c9d7cf2bea50e47638c63effa72a5059fdb4e58`. No experiment allocation, model, GUI, IPC or input call was made. The returned V7 result is preserved in `results/result-07.json`. Important provenance correction: the actual V7 invocation was run using `docker exec` in a temporary, already-running container after copying the checkout into it. That container had been started without explicit network isolation, read-only mode, CPU/memory/PID limits, or a read-only bind mount. `FREEZE_V7.json` incorrectly describes planned controls as if they were applied; it is retained unchanged as a discrepant freeze record, not accepted proof of those controls.
- **D:** The independent filesystem-level recount passed: 14 image-model result files match the 14 image-call descriptors and their usage; three fresh preflight gate records match trace usage; 18 task rows each have one exact append-only submission; 14 image-call IDs are unique; cumulative input and generation arrays reproduce the report; task-4 persistent repair succeeds after old reference `MISSING` with zero stale pointer admission; and the stored usage totals reconcile exactly. Reconstructed input totals are plain 63,128, ephemeral 63,779, persistent 26,563; total input 153,470, cached subset 4,864, output 2,435, reasoning output 837. Token break-even first occurs at task 2.
- **C:** Docker Desktop 28.5.1 and `desktop-linux` were observed. The run used the locally pinned image digest `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9` (`linux/amd64`), but explicit offline/read-only/resource controls were **not** applied to the successful invocation. The independent recount imports no project runtime modules and its code performs no network operation; however, the execution environment itself did not enforce network isolation. The result therefore supports computational reconstruction, not a claim that the stated isolation/resource controls were experimentally verified.
- **U:** This is a bounded data-integrity/accounting reconstruction, not a replication, second sample, independently scored screenshot judgement, provider-level proof of preflight call IDs, or broad runtime/product claim. The original one-sequence-per-arm timing remains descriptive. Because the V7 container controls were not enforced, treat it as a Docker-executed local recount, not a fully constrained container audit.

## Retained auditor construction failures

The independent auditor had six successive construction attempts before V7 returned PASS. These were auditor-development attempts, not experiment retries, and did not alter the source allocation. The exact source files for V1–V6 were overwritten and are not preserved. Their complete Docker output files were not copied out and cannot be recovered. `results/failed-audit-output-transcript.md` is explicitly a transcription of tool responses, not a raw Docker log. The contemporaneous errors were: V1 `KeyError: 'call_id'`; V2 task-6 input mismatch for plain; V3 `KeyError: 'cumulative_generations'`; V4 generation mismatch from omitting preflight generation; V5 generation mismatch (recomputed `[1,2,3,4,5,6]`, reported `[2,3,4,5,6,7]`); V6 input mismatch after double-counting preflight. Freeze descriptors are local untracked files, not committed evidence. V1–V7 source snapshots were not retained. V7's freeze also misstates the actual container controls, as noted above.

The V7 recount initialized task-local input to zero and added each arm's preflight usage exactly once to every cumulative endpoint; it initialized cumulative generation count to the one preflight generation. It matched the report arrays exactly. The failed source revisions and original Docker output files for V1–V6 are not retained; only the labeled transcript is available.

## Decision-rule scope

The official preregistration freezes one sequence per arm, and its `decision.hold` field names comparability/accounting failure or a formal discovery invalidating the allocation. It does not state that one sequence is insufficient. The integration plan separately says HOLD applies if the single allocation is insufficient. The live report correctly describes the timing as a single-sequence descriptive observation, but claims a scoped RETAIN under its preregistered token/correctness gates. This audit does not retroactively rewrite that result. It flags the plan/preregistration decision-rule mismatch and does not generalize the one-run result; a future study requires a new, prospectively frozen rule and allocation.

## V8 constrained recount (2026-09-28)

V8 is a separate one-shot reconstruction against the same immutable evidence, not a new experiment or replication. It was executed with Docker Desktop 28.5.1 (`desktop-linux`) and the locally present Python 3.12 image pinned by digest. The actual command enforced `--network none`, read-only source bind, output-only writable bind, read-only root filesystem, bounded `/tmp`, CPU 0.10, memory 128 MiB and 16 PIDs. The auditor source is pinned by SHA-256 in `FREEZE_V8.json`; its freeze is passed explicitly as the third program argument. The only output is `results/run-08/result.json`.

Result: `PASS_SCOPED_EVIDENCE_RECOUNT`. All four frozen evidence hashes match; 14 image-call raw results match trace IDs and usage; 3 fresh preflight records match; 18 task rows each map to one exact submission; cumulative input/generation arrays, repair and stale-pointer gates, and aggregate usage reconcile with the retained report/audit. Reproduced totals remain plain 63,128, ephemeral 63,779, persistent 26,563 input tokens; total input 153,470, cached subset 4,864, output 2,435, reasoning 837; break-even remains task 2. No model, GUI, IPC, or task input call occurred.

This V8 evidence supersedes V7 only as evidence that the recount can be run under the stated enforced container controls. V7's original provenance discrepancy remains visible and unchanged below; V8 does not retroactively validate V7 controls or repair the historical preregistration/plan decision-rule mismatch.

## Evidence

- Frozen successful run: `FREEZE_V7.json`
- Independent auditor source: `independent_recount.py`
- Returned V7 recount object: `results/result-07.json`
- V8 enforced-container freeze and output: `FREEZE_V8.json`, `results/run-08/result.json`
- Transcribed V1–V6 tool errors (not original Docker logs): `results/failed-audit-output-transcript.md`
- Immutable upstream preregistration/trace/report/audit SHA-256 values are in the freeze file and result.

No change is made to the original experiment conclusion or allocation. This audit only increases confidence in the integrity of its retained counts and exact-submission records.
