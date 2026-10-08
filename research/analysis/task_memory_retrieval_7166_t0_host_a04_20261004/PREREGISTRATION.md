# Preregistration — TASK-MEMORY-RETRIEVAL-7166-T0-HOST-A04-20261004

## Lineage and intake

A04 is a separate allocation after A03 `FAIL_METHOD` (#7166 comment
#5976328577). A03 and its raw outcome stay unchanged. Base main is
`58bcbb4c45501880db8782158ddd3add3b765984`; #7166 remains open. A04 reuses the
same fixture semantics but uses a new auditor/test contract that rejects no-op
corruptions before scoring. This is not a rerun or silent repair of A03.

## H / T / D / C / U

- **H:** Under this finite authored selector, current-only selects `NONE`,
  exact source-bound linear history selects `EVENT_CHAIN`, ambiguous,
  provenance-incomplete, forked/conflicting cases abstain; no row grants action
  authority. All six changed corruptions, including a real wrong label, are
  rejected by the independent auditor.
- **T:** 72 cases (six strata × 12), candidate reads fixture only, separate
  oracle; construction tests and `py_compile`, then one candidate invocation
  and—only after exit 0—one raw-only auditor invocation. Auditor proves each
  mutation differs bytewise before checking rejection. Six controls: wrong
  label, source hash, ambiguous identity, authority grant, dropped event, forked
  lineage.
- **D:** `PASS_METHOD_SCOPED` only if 72/72 rows reconstruct, every mutation is
  proven to change raw content and all 6/6 are rejected, with zero authority
  grants. Any no-op, acceptance, malformed output, or mismatch is FAIL. Source
  or main movement before candidate is STOP. Retries=0.
- **C:** Deterministic authored fixture and oracle; A03 showed mutation-suite
  PASS without effectiveness assertions is insufficient.
- **U:** No natural retrieval utility, model behavior, actual model-visible
  cost, task effect, GUI, latency, runtime, or product inference.

## Runtime and commands

Host-only macOS arm64 / CPython 3.14.5 / standard library. Do not retry the
same-day OrbStack content-store failure already recorded at #7383 comment
#5976132398; no container enforcement is claimed. No model, GUI, network, GPU,
external resource, or input. Output path must be absent at launch. Candidate and
auditor budgets 1 each, retries/substitutions 0.

From repository root:

```sh
python3 -I research/analysis/task_memory_retrieval_7166_t0_host_a04_20261004/candidate.py
python3 -I research/analysis/task_memory_retrieval_7166_t0_host_a04_20261004/auditor.py
```

Post this preregistration and freeze hashes to #7166 before candidate
invocation. Auditor runs once only if candidate exits 0.
