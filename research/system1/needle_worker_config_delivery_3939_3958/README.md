# Worker configuration: a retained STOP and a completed HOLD

Issues: #3911 (historical FAIL), #3939 (monolithic STOP), #3958 (completed three-batch HOLD).
Intake/source main: `b2457b746a6df06f6536585dfe2ab937aff639f4`.

## Result

**HOLD_THREAD_MECHANISM_NOT_EXPOSED** on #3958. All three fresh seed batches completed with 15/15 worker exit-0 rows and 3/3 references. The frozen independent standard-library auditor returned zero evidence, source or manifest errors and rejected all six registered corruption controls. Its output SHA-256 is `5f04b4183b3ebd2dba78b92897329f689a595cc13a0e54dcdd6be9f201348e3a`.

The source gap is real: the historical `run_seed()` sets `torch.set_num_threads(1)` and `torch.use_deterministic_algorithms(True)`, but `--resume-worker` enters `worker()` without those setters. Source blob `69a9266981d11eaffc7dc84349356a183b77207b` is preserved byte-identically inside both bundles; SHA-256 `ae12bc6b7fee156bc04ea701fa939313d0db5b5c6eb600daa2153662d82e055c`.

H1 is supported in this environment: DEFAULT fresh workers report five intra-op threads and deterministic=false, while their parents report one and true. H2 is also supported for the first arrival: all three explicitly aligned workers match the reference. But **every one of the fifteen workers, including the default and five-thread controls, has identical full state, float32 logit bits and predictions**. The contrast needed to explain the old numerical mismatch is absent. Neither an aligned-worker match nor the source gap establishes historical causality.

| Worker mode | Intra-op threads | Deterministic | State exact | Logits bit-exact | Changed predictions |
|---|---:|---|---:|---:|---:|
| DEFAULT | 5 | false | 3/3 | 3/3 | 0 |
| T1_D0 | 1 | false | 3/3 | 3/3 | 0 |
| T1_D1 | 1 | true | 3/3 | 3/3 | 0 |
| T5_D0 | 5 | false | 3/3 | 3/3 | 0 |
| T5_D1 | 5 | true | 3/3 | 3/3 | 0 |

Inter-op threads remained five. Each reference has 4,096 rows x four logits; all 245,760 worker logit scalars match their paired references. The independent auditor reconstructs exact state comparisons, float32 bit patterns, labels and argmax from retained bytes; it does not independently regenerate AdamW trajectories or validate PyTorch's random generator implementation.

## Preserved failure and execution history

#3911 remains scientific FAIL: its prior report had exact adapter/AdamW/cursor state and matching predictions, but non-bit-exact logits (up to 3.82e-6) and update-only p95 above 60 ms. This study uses another PyTorch version/environment and only arrival one; it cannot repair or relabel that result.

#3939 remains **STOP_EXECUTION_ENVELOPE_INCOMPLETE_DENOMINATOR**. The first interactive tool transport was unavailable before shell launch; absence of output/processes confirmed no formal invocation. The frozen synchronous CLI was then invoked once and the tool reported timeout at its requested 120-second envelope. Inspection found no surviving experiment process. Nine worker exit-0 rows were retained: five for3912101 and four for3912102. There is no final COMPLETED/MANIFEST or outer exit receipt. The unchanged auditor exits1 because MANIFEST.json is missing. Its exact traceback is retained. No old seed was retried or pooled. A posthoc RETENTION_MANIFEST is explicitly not an original completion manifest.

#3958 changed serialization granularity and fresh seeds only. It used three immutable batches3912201/3912202/3912203, each invoked once, then one raw-only aggregation and one frozen audit. Each batch retained all five modes before returning to the execution tool. Source hashes were posted to the issue before invocation. The old partial diagnostic and all nine no-difference rows remain visible, never counted in the new denominator.

## H / T / D / C / U

**H:** Fresh exec workers do not inherit process-local PyTorch settings; explicit matching configuration may restore exact outputs. The secondary thread mechanism requires both one-thread arms exact AND a multithread logit difference with unchanged states/predictions.

**T:** Per new seed: exact predecessor synthetic8-feature/hidden16/rank2 family,512-row base with400 AdamW updates, one sealed starting checkpoint, eight first-arrival updates,4,096 heldout rows, one in-process reference and five fresh exec workers. The unmodified predecessor CLI is called after wrapper configuration. Cyclic arm rotations0/1/2 are only partially balanced, not a Latin square. No training or threshold changes after the freeze.

**D:** Same-config mismatch would be FAIL; missing evidence would be STOP/HOLD; the full registered numerical contrast would be scoped PASS. Here H1/H2 pass their component checks but the thread mechanism remains HOLD because all arms agree. Audit integrity PASS cannot become scientific mechanism PASS.

**C:** Provided Linux x86_64 execution container; CPython3.13.5; PyTorch2.10.0+cpu; five reported CPUs, default intra/inter-op5/5, deterministic=false. Docker/Podman and GPU are absent. No installations, provider/model-service requests, GUI, OS input, shared runtime edits, or historical allocations. This is not a Docker Desktop/OrbStack/PyTorch2.5.1 replication. The legacy allocation field remains in the original checkpoint schema only; wrapper allocation IDs and fresh seeds identify these separate studies.

**U:** Not a whole16-arrival stream result, historical causal explanation, general reproducibility claim, model-quality or GUI result, runtime promotion, or human-tempo benefit. PyTorch documents that reproducibility is not guaranteed across releases/platforms and that thread configuration must precede tensor work. The next useful causal test belongs on the original pinned2.5.1 container with complete parent/worker configuration receipts, not another numerical pass on2.10.

Primary documentation: PyTorch2.10 `notes/randomness.html`, `notes/numerical_accuracy.html`, and `generated/torch.set_num_threads.html` under `https://docs.pytorch.org/docs/2.10/`.

## Timing is not a performance acceptance claim

| Mode | Update-only ms, three seeds |
|---|---|
| DEFAULT | 6.1108,6.8059,10.2559 |
| T1_D0 | 4.8402,4.2167,4.9002 |
| T1_D1 | 14.2590,4.9706,5.0228 |
| T5_D0 | 6.4612,16.0703,5.3290 |
| T5_D1 | 9.9831,23.3426,5.4511 |

Fresh-process wall time spans2.571-3.968seconds and is distinct from update-only time. Three samples per arm, partial order balancing, host load and environment changes prohibit a reliable tail/speed claim. No p95<=60ms acceptance is asserted.

## Evidence delivery and independent recheck

The original complete verbatim tar.xz artifacts were hashed before publication encoding:

| Original archive | Files | Uncompressed bytes | Archive bytes | SHA-256 |
|---|---:|---:|---:|---|
| needle_resume_worker_config_v1.tar.xz | 93 | 5,398,286 | 843,632 | d4b7738efc0ab2e4b7392eacae08cbeb4d70e2fcad9aaad16b80d23cfc81d3b6 |
| needle_resume_worker_config_batches_v2.tar.xz | 145 | 8,615,528 | 1,234,884 | 06f757038d563a45520d772175eb1a87abba56aeda7cede2719c7ced79cac1a5 |

The GitHub capsule is **byte-bound numerical reconstruction, not a platform-independent verbatim archive**. Source, state, process/configuration/timing receipts, hashes and logs are stored as literal bytes. Five seeded fixture arrays and29 heldout records use deterministic reconstruction recipes. The decoder generates fixtures and performs five cached forward computations from frozen tensors; it never trains, invokes a worker/experiment or reruns an allocation. Every decoded file must match its ORIGINAL pre-packaging size and SHA-256; any numerical/platform discrepancy is a hard STOP. Original complete archives are separately delivered with the research handoff. The capsule does not authorize treating newly calculated unverified arrays as old evidence.

In the execution container, an independent comparison verified **all238 decoded files /14,013,814 bytes** against the original tar members byte-for-byte. Repacking recreated both original tar.xz bytes and hashes exactly. The unchanged raw auditor on decoded #3958 evidence reproduced the same AUDIT.json hash above. `BYTE_COMPARISON.json` and `DECODE_RECEIPT.json` retain these publication-only checks. Formal sources were never edited for packaging.

With compatible PyTorch2.10.0+cpu already installed:

```sh
python decode_capsule.py CAPSULE_PARTS.json /absolute/fresh/decode-output
python /absolute/fresh/decode-output/needle_resume_worker_config_batches_v2/audit.py /absolute/fresh/decode-output/needle_resume_worker_config_batches_v2/formal-01 --output /absolute/fresh/audit-recheck.json
```

The first command refuses an existing output directory. Review decoded `FREEZE.json`, `experiment.py`, `worker_entry.py`, `aggregate.py`, `audit.py`, construction outputs, raw manifests and exact commands. For #3939, inspecting the absent completion manifest and retained auditor traceback is the intended STOP verification; do not synthesize completion files. Do not invoke an experiment command merely to inspect the archive.

## Integration handoff and roadmap status

Completed scoped roadmap: repository/source intake; closed-issue residual identification; H/T/D/C/U registration; no-training construction; source freeze; first formal STOP retained; separately registered immutable-batch successor; complete raw audit and controls; byte-bound evidence delivery.

PR publication, review and merge are separate from these scientific outcomes. This branch contains additive research evidence only. **No runtime setting should be changed on this result.** It does not remove a demonstrated blocker in the six-task usable-desktop integration spine and must remain research/backlog evidence rather than product progress. The broad ROADMAP, live matched-model measurement, original-environment causal test and production promotion remain open.

Reconnaissance covered main/README/CURRENT_GOAL/ROADMAP, branch collection, recent open/closed Issues and PR collection, and targeted3911/thread search. Large inventories were paginated/truncated and one search rate-limit occurred; ownership was targeted, not exhaustive. Unrelated active #3929/#3931 and all prior evidence/branches were not modified. Delete only our own delivery branches after merge/retention/dependency verification and only through a supported safe operation.
