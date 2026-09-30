# Constrained interaction testing — Issue #5330 T0

## H / T / D / C / U

**H.** On this explicitly synthetic finite workflow, a deterministic pairwise covering array can expose a known two-factor unsafe interaction that a deterministic one-factor-at-a-time (OFAT) design misses, at lower test-case cost than exhaustive enumeration. A deterministic three-way extension should expose a separately planted three-factor interaction while using fewer rows than exhaustive enumeration. This is a design-method sensitivity check, not evidence about repository runtime hazards or real-world failure rates.

**T.** One containerized, standard-library-only Python run. Factors are (1) observation freshness {current, stale}, (2) lease {valid, expired}, (3) responsibility {single, overlap}, and (4) delivery {once, duplicate}. There are 16 full assignments. Compare OFAT (baseline plus each single-factor change, 5 rows), deterministic pairwise coverage, and exhaustive coverage. Separately compare a deterministic 3-way covering design with exhaustive coverage. The synthetic oracle labels only `stale × expired` as a pair hazard and only `stale × overlap × duplicate` as a triple hazard; these are planted diagnostic controls, not derived safety claims. Record exact assignments, pair/triple coverage, detections, rows, and independent oracle reconstruction. No application, model, GUI, network, or external action.

**D.** `PASS_DESIGN_SENSITIVITY_ONLY` iff the generated pairwise set covers all 24 value-pairs and triggers the planted pair oracle that OFAT misses; the generated 3-way set covers all 32 value-triples and detects the planted triple oracle; both designs are deterministic and strictly smaller than the 16-row exhaustive design; and an independent raw-only audit reconstructs every assignment, coverage count, oracle label, and aggregate. Otherwise preserve `FAIL_*` or `STOP_*` as emitted. No statistical or runtime generalization.

**C.** Binary factors are modeled as independent solely to make the synthetic design finite. The planted oracle intentionally makes design sensitivity observable. Factors are not claimed independent in Agent Interface. Coverage here is exact for this finite binary fixture. Deterministic greedy set cover is the named generator; no random seed is needed. `python:3.12-slim` image is pinned by digest in `FREEZE.json`; container runs as its default unprivileged user, read-only root, no network, no capabilities, and a read-only source mount plus a dedicated output mount.

**U.** Real factor dependencies, realistic hazard prevalence, relation validity, detection under unknown oracles, human/backend effects, schedule/state dependence, interaction strengths beyond three, and usefulness against authentic repository failures remain unknown. This T0 cannot authorize fault injection against an application/runtime.

## Definitions

Each factor uses levels `0` and `1`. OFAT is all-zero plus four assignments with one flipped factor. For strength *t*, enumerate candidate rows in lexicographic order and greedily select the row covering the greatest number of still-uncovered *t*-tuples; ties resolve to the first candidate. This deterministic minimum-selection rule is frozen for reproducibility but does not claim a globally minimum covering array. Exhaustive evaluates all 16 assignments.

The pair oracle is exactly `freshness=1 AND lease=1`; the triple oracle is exactly `freshness=1 AND responsibility=1 AND delivery=1`. These synthetic controls test whether designs can expose interactions of the declared strength, not whether those predicates are unsafe in a real system.

## Artifacts

- `design.py`: deterministic designs, coverage, and synthetic oracle.
- `run.py`: single frozen invocation; writes `raw.json` and a generated summary.
- `audit.py`: separate raw-only reconstruction (does not import the generator or runner).
- `test_design.py`: construction tests; not a formal allocation.
- `FREEZE.json` / `FREEZE_COMMENT.md`: exact source, image, run boundary and one-shot command.
- `results/formal-01/`: immutable first formal outcome and independent audit.
