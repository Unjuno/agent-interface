# Preregistration — TASK-MEMORY-RETRIEVAL-7166-T0-HOST-A03-20261004

## Intake and ownership

- Repository: `Unjuno/agent-interface`; frozen base: `58bcbb4c45501880db8782158ddd3add3b765984`.
- Issue #7166 is open. Exact GitHub MCP searches found no open PR or branch matching 7166. A01 remains `STOP_STALE_MAIN_BEFORE_CANDIDATE`; A02 remains preregistered with candidate/auditor 0/0. Neither predecessor is modified or rerun.
- This is a new allocation and additive path, not an A02 recovery or relabel.
- Adjacent #5947 old-state interference and the separate retrieval-feedback proposals in #7166 comments are not tested.

## H / T / D / C / U

- **H:** For this deterministic authored selector, current-only tasks yield `NONE`; exact source-hash-bound linear history yields `EVENT_CHAIN`; ambiguous identity, missing provenance, forked/conflicting lineage, or hash mismatch yields `ABSTAIN`; no row grants action authority.
- **T:** 72 rows, six strata × 12. Candidate reads only `fixture.json`; the independent expected-case inventory is in `oracle.json`. Run construction tests and byte-compilation before formal invocation. Then execute candidate exactly once, and auditor exactly once only after candidate exit 0. The auditor imports no candidate module and checks six frozen mutations.
- **D:** `PASS_METHOD_SCOPED` only if all 72 case identities, labels, source hashes and event lineage reconstruct exactly, authority is false/empty in every row, and all six corrupted-output controls are rejected. Any mismatch is retained as FAIL; missing or changed preconditions are STOP. Retries=0.
- **C:** Small deterministic authored fixtures and a finite independent oracle test the method/data contract only.
- **U:** Natural retrieval quality, model behavior, actual model-visible cost, task effects, GUI, latency, runtime, and product benefit remain unknown. No efficiency or generalization claim is permitted.

## Environment and limits

Host-only macOS arm64 / CPython 3.14.5 / standard library. The same-day OrbStack content-store failure is already recorded at Issue #7383 comment #5976132398; do not retry Docker, pull/build an image, or claim container enforcement. This CPU-only contract fixture has no container-specific requirement. No model, GUI, network, GPU, external resource, or input call. Output path must be absent at launch. Candidate and auditor budgets are one invocation each; retries/substitutions=0.

## Frozen commands

From repository root:

```sh
python3 -I research/analysis/task_memory_retrieval_7166_t0_host_a03_20261004/candidate.py
python3 -I research/analysis/task_memory_retrieval_7166_t0_host_a03_20261004/auditor.py
```

The auditor command is permitted once only if candidate exits 0. Raw stdout,
exit codes, and output hashes must be recorded. This preregistration must be
posted to Issue #7166 before candidate invocation.
