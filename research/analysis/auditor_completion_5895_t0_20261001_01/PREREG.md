# Issue #5895 — strict runner-completion semantics T0

Allocation: `AUDIT-COMPLETION-5895-T0-ISOLATED-ORB-20261001-01`
Frozen main at formal start: `4b7fe7837e4ee8c0d035ebfbf52baf014f042295`
Frozen target: open PR #5630 head `288d0498d11cf16657e523a04616bf4f49cd94f4`; frozen copies were independently hash-checked against the preparation in PR #5899.
Execution: one isolated OrbStack Ubuntu amd64 guest; Docker Engine inside guest; one fresh candidate and (only on candidate exit 0) one independent audit container; both network disabled.

## H / T / D / C / U

**H.** The frozen synthetic CLI auditor selects `runner_complete` rows using `exit_code == 0` before cardinality validation. Python equality may accept Boolean `false`, float `0.0`, and one successful row alongside a failing completion row; null, string "0", missing code, and duplicate success should be rejected.

**T.** Run the exact frozen target CLI against eight raw JSONL cases in fixed order: pristine integer-zero control; Boolean false; float zero; null; string zero; missing exit code; duplicate success; integer-zero plus integer-one. Expected target exits: `[0,0,0,1,1,1,1,0]`. The candidate orchestrator executes each target invocation once and retains each raw, target audit JSON, stdout/stderr, exit, and full manifest. If and only if the orchestrator exits 0, run the independent raw-only auditor once in a separate container. No retries. The upstream #5899 orchestration/auditor are copied exactly except both allocation literals are rebound to this fresh #5895 allocation; the frozen target auditor, expected fixture, and fixture builder are byte-identical to their #5630 source blobs.

**D.** `METHOD_REPRODUCED_SCOPED` only if candidate exits 0 with the exact preregistered exit vector, candidate manifest names this fresh allocation, independent audit verifies target Git blobs and SHA-256 values, exact completion rows, unchanged baseline non-completion rows, all raw/audit/stdout/stderr hashes, complete inventory, and reports `PASS_INDEPENDENT_RAW_AUDIT` with errors empty. Any mismatch is retained without tuning. Source, image, provenance, resource, or output gate failure before candidate is `STOP_NOT_EVALUATED`. If candidate runs and returns unexpected exits, preserve the candidate output as `FAIL_METHOD`; follow the upstream rule to run the independent auditor only after candidate exit 0.

**C.** One deterministic synthetic JSONL CLI boundary, one pinned CPython 3.12 slim image (`sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, `linux/amd64`), no network/GPU/model/X11/GUI/input/game/task-effect.

**U.** This can reproduce a Python equality/cardinality defect in one synthetic runner-completion auditor only. It does not validate PR #5630's formal X11 provenance boundary, physical key-up timing, keymap, GUI/game behavior, safety, efficacy, latency, MAP01 occupancy, or Issue #59.

## Resource and source integrity

Fresh branch and output namespace; do not use or modify PR #5899's package or STOP. `source/` holds byte-exact upstream source copies; the only adaptations are candidate/audit allocation literals. The image is a verified OCI multi-platform index with a linux/amd64 manifest. Candidate and auditor mount source read-only, output writable only, read-only root, no capabilities, no network, one CPU, 512 MiB, 64 PIDs. Candidate/auditor counts 1/1 maximum; retry 0.
