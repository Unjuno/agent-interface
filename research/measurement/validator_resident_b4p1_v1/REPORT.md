# Static-validator process lifetime cost — Issue #4364

PASS_RESIDENT_STATIC_VALIDATION_COST_SCOPED

## Result and chronology
Public source freeze 0caefdc5bd8ef6a7a9d8da39dee3c76996b14e31 and comment5832573808 preceded all three measured batches. First-result comment5832598534 preceded packaging. Same source/gates throughout; 17 frozen members unchanged. One retained allocation, no retries, replacement, exclusion or postfreeze tuning.

All21 paired repetitions /42 measured sequences /574 responses /308 worker exits completed. Status counts: {'valid': 294, 'invalid': 140, 'input_error': 140}. Three supervised batches exit0. Warmup82 responses/44 workers and construction are excluded, but retained. Every stdout equals the fixed report oracle and matched partner; file rewrite/removal is visible. File contents are not cached.

## Wall time, median [minimum, maximum] milliseconds

| Requests | Fresh total | Resident total | Median paired ratio | Fresh first | Resident first |
|---|---|---|---|---|---|
| 1 | 40.618 [36.663, 46.364] | 40.088 [37.924, 47.731] | 0.936899 | 34.729 [31.379, 40.418] | 34.254 [31.938, 40.482] |
| 8 | 311.877 [303.816, 319.412] | 41.851 [40.238, 43.682] | 0.133391 | 33.063 [32.161, 36.040] | 33.490 [32.834, 35.673] |
| 32 | 1291.336 [1251.982, 1336.605] | 48.127 [47.374, 53.108] | 0.037828 | 33.766 [31.947, 45.178] | 33.920 [32.885, 34.766] |

Paired ratios are medians of the seven within-pair ratios, NOT ratios of displayed medians. Length1 is an equal-work control; its variation is not a supported speedup claim. Both predeclared length8/32 <=0.50 gates pass. First reply still needs cold interpreter/import time.

## Environment and endpoints
Linux6.18.44 x86_64, CPython3.13.5/GCC14.2.0, AMD EPYC9V74 reported by guest, affinity CPU0 inherited by parent/children, one outstanding request, sequence batch sizes1/8/32, seven technical repetitions each. Frequency/load are not fixed; no hardware exclusivity or Docker image attestation. Standard library only, -I -S -B; display and Python path environment removed. This is a local validation-service endpoint, not full CLI/MCP or model/task performance.
Total wall begins before first file update/process creation and ends after final report AND process exits. It includes file updates, interpreter/import, validation, pipe transfer and shutdown. Response latency excludes following shutdown. Child CPU is independently read from RUSAGE_CHILDREN; all original brackets/samples are retained. Warmup and retention/audit after end are excluded as planned. No timing is calibrated; no combined u_c or coverage k is fabricated.

## Integrity and limitations
Raw-only auditor imports no worker/validator/runner.4839 checks/errors0, exit0 and empty stderr; eight effective well-formed mutations reject. Counterexample mutations cover stale report, missing output/exit, wrong PID, task-success injection, reversed clocks, changed input and relabelled warmup. Eight construction unit methods passed. Same-author separately implemented audit is not independent human review.

Both modes run identical research worker code. Fresh starts one worker per request; resident starts one per finite sequence. This is not a comparison of the official zipapp command versus a different result implementation. Existing inspect_file and four dependencies are exact current-main bytes. Generated empty runtime initializer avoids dispatch package initialization. No existing runtime/default/CLI/zipapp source is edited.
No result cache, input action, lease grant, GUI or model evaluation. Static-valid requests include an expired lease by design; live admission remains not_evaluated. Process reuse also changes import and interpreter allocation lifetime; isolated attribution to a single OS mechanism is not justified. Sustained memory growth, concurrent clients, queueing, process/reader crash, source upgrades, arbitrary filesystem mutation, service authentication, power loss, model repair and task utility remain untested.

Measured request metadata: 64736 bytes; JSON reports: 244062 bytes. These are not model-token counts or image budgets. Same path/content at each position is used by both modes. Retained raw records include exact stdout, stdin recipe, argv, PIDs, exits, source/input hashes and timings; no responses are regenerated for publication.

## Preserved construction failure
Construction01 completed two length8 sequences but passed a relative path after cwd changed. It returned INPUT_UNREADABLE on14 extant-file requests; raw audit exit1 remains unchanged and is byte-reproduced. Controls aborted at the failed baseline. Its original source and raw data are retained. The path was normalized before new construction02 and source freeze. Construction02 passes128 checks/eight effective controls. Unit-created temporary fixture files are not retained; their exact fixtures and unit source plus stdout/stderr are retained. Initial construction launcher PID was not separately saved; that limitation is not extended to measured batches, whose launcher/process exits are saved.

## Integration decision and remaining roadmap
For repeated local static checks, a finite reused worker is a promising opt-in engineering direction; this result does not justify replacing all CLI calls or introducing an always-on mandatory service. Preserve existing behavior and later test actual caller integration/lifecycle and model correction before making task-efficiency claims. #3850/#2 and global ROADMAP stay open.
Read-only source/raw publication, exact remote readback, applicable CI and scoped review precede evidence-only main merge. Prior metadata-only STOPs and blocked source are not included or retried.

## Evidence units / conditional proof
PLAN.md gives the complete declared semantic argument, H/T/D/C/U, variables and unit check. Times are integer ns in raw records, converted to ms by1e6; ratios divide like time units and are dimensionless. Byte counts and CPU time remain separate. No theorem proves the observed speed independently of the measured environment.
