# Issue #4083 — real exact-crop dependency-closed partial recompute

## Result

`PASS_EXACT_CROP_PARTIAL_RECOMPUTE_CONTRACT_SCOPED` and
`PASS_EXACT_CROP_PARTIAL_RECOMPUTE_COST_SCOPED` on fresh allocation 03.

The candidate is a research-only cache around the unchanged real
`exact_crop_semantic_probe_v1.py`; no shared runtime source was edited. Across
9 cases / 216 requests, every candidate result exactly matched a fresh baseline
`score_path` result and every result kept `grants_input_authority=false`.

| workload | median candidate/baseline CPU | range | candidate recomputation pattern |
|---|---:|---:|---|
| METADATA | 0.0450 | 0.0419–0.0489 | 1 frame + 1 crop recomputed; 23/23 reused |
| ROI | 0.0515 | 0.0464–0.0519 | 1 frame + 4 crops recomputed |
| IMAGE | 0.1094 | 0.1089–0.1157 | 4 frames + 4 crops recomputed |

The frozen primary gate was METADATA median CPU ratio <= 0.75, so the measured
0.0450 passes. This is not a 22x end-to-end speedup claim: it is a local process
CPU ratio for 24 already-authored verification requests on deterministic images.
Imports, process startup and fixture generation are outside timing; exact image
file read + SHA-256 version maintenance stays inside candidate timing.

## H/T/D/C/U

- **H:** exact artifact bytes and exact ROI identify the expensive decoded-frame
  and crop-hash nodes; metadata-only changes can reuse them without stale output.
- **T:** METADATA/ROI/IMAGE x three repetitions, 24 requests per case, separate
  fresh worker processes, baseline/candidate balanced order. Source/gates were
  published before the first successful complete allocation.
- **D:** exact result equality is mandatory. The cost gate is separate and cannot
  rescue any semantic mismatch. Audit v2 reconstructs 657 checks and rejects
  10/10 evidence corruptions.
- **C:** synthetic PNGs, one process-local single-owner cache, SHA-256 integrity
  keys only. Host scheduling and PNG workload shape can affect timings.
- **U:** no live GUI/model/task, tokens, concurrent cache, eviction, memory-growth,
  authentication or production claim.

## Variable table and unit check

| symbol | meaning | SI unit | definition | domain | type |
|---|---|---|---|---|---|
| B | baseline process CPU time per 24-request case | s | process-time interval | >0 | scalar |
| C | candidate process CPU time per 24-request case | s | process-time interval | >0 | scalar |
| R | CPU ratio | 1 | C/B | >0 | scalar |
| N | requests per case | 1 | fixed 24 | 24 | integer |

The gate uses `R=C/B`; seconds divide by seconds, so `R` is dimensionless.

## Preserved failures / execution history

1. Allocation 01: `STOP_OUTPUT_PATH_PREEXISTED_EMPTY`, zero scientific cases.
2. Allocation 02: `STOP_EXTERNAL_EXECUTION_ENVELOPE`; 7 complete cases, one
   partial, one unstarted. These rows are retained but never pooled.
3. Allocation 03: three fixed 3-case batches, all nine case exits 0 and all three
   observed tool batch exits 0; allocation terminal receipt is complete.
4. Frozen audit v1: `STOP_AUDITOR_EXECUTION_ENVELOPE`; zero verdict output.
   Postformal `audit_v2.py` is separately hash-frozen and audits retained raw only.

The audit-v2 child itself wrote exit 0 and a complete result. The surrounding
container tool reported nonzero after that receipt; this transport anomaly is
kept separate rather than rewriting the child exit.

## Evidence integrity

Frozen upstream Git blobs:
- `22a5c022d613039b0386535304cbc432009699af`
- `f4a68e95e6bbeb2896a00168f0c88282551be4e4`

Preformal `FREEZE.json` SHA-256:
`c3b6a5cdc5665a3160c0508ebaf5cddb6b12a5faec16a0b5ab5a99680beda8f2`.

Audit-v2 source SHA-256:
`0257121afee65edcc972591a438d9f8ef1193b5b3c6d9a53f30aa04cc3eefb28`.

Complete evidence capsule SHA-256:
`aa5be683d71aaf3ee7d4931bcf101257d914b9ef2a09ad5e817fc6c26bd2df43`.
Expected Git blob: `70cbcb361913776269e364567e6ea780a80f6803`.

Independent audit here means a separately structured implementation/process by
the same author, not independent human review or second-machine replication.
