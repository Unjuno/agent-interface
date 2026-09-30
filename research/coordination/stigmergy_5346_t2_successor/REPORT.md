# Issue #5346 T2 — scoped finite-model PASS; live transfer untested

**Disposition: `PASS_SCOPED_FINITE_MODEL`; Issue #5346 remains open.** With a
shared atomic admission gate held fixed, fresh advisory markers reduced blocked
proposal attempts in the finite schedule model without changing any admitted
lease/effect/completion trace. Local markers traded less contention reduction
than central claims for zero *explicit central-claim messages* in this metric.
This supports only a bounded synthetic tradeoff, not a deployable stigmergy
mechanism.

## Relation to T1

T1 remains unchanged at
[`../stigmergy_5346_t1_successor/REPORT.md`](../stigmergy_5346_t1_successor/REPORT.md)
and retains `STOP_HARNESS_INVALID`: a crashed owner's lease was released at task
duration 2 instead of frozen TTL 3. T2 is a separately preregistered and
expanded TTL-boundary successor, not a reinterpretation of T1 or an overwrite
of its raw/audit.

## H/T/D/C/U result

- **H:** Supported only for the tested deterministic model: advisory local
  markers reduced blocked attempts versus no coordination in fresh-delivery
  strata; all three policies had identical lease/effect/completion traces.
  Local markers used fewer explicit central-claim messages than the central
  arm, but the local-marker writes/reads themselves are not counted as explicit
  messages.
- **T:** 1,600 schedules × 3 arms = 4,800 rows. Workers 2–4; every arrival
  permutation; marker/observation delay 0–4; clean/lost/duplicated/stale/forged
  local marker conditions; owner completes/crashes. Lease TTL=3, task duration=2,
  crash at tick 1. One pinned-container invocation; no retry.
- **D:** Both independent raw-only audits PASS. The first auditor found 4,800
  rows/1,600 schedules, zero errors, 0 unsafe admissions, 1,600 completions,
  and exactly one recovery in each of 800 crash schedules. The supplemental
  auditor independently validated observation delay, expiry, marker fault
  behavior, and suppression timing. It rejected an early-observation mutation;
  the first auditor rejected TTL-release and marker-authority mutations.
- **C:** Pooled across all frozen strata, blocked admissions were NONE 3,700,
  LOCAL_MARKERS 3,264 (436 fewer; 11.8%), and CENTRAL_CLAIMS 2,610 (1,090 fewer;
  29.5%). For fresh clean/duplicated markers, delay 1 yielded local 108 vs NONE
  296 blocked attempts; delay 2 yielded 236 vs 296. At delays 3 and 4, markers
  were expired/unseen and local blocked attempts equaled NONE (296). Central
  claims blocked 2,610 attempts overall, but emitted 4,300 explicit
  coordination messages; local and NONE each emitted zero in this narrow
  explicit-message counter. The local marker writes, visibility, storage,
  serialization, and observation costs were not measured or counted as messages.
- **U:** Strategic or adaptive worker behavior; empirical delivery loss or
  latency; clock skew; real target identity, UI visibility, and external
  mutations; actual coordination bandwidth/cost; any wall-clock or model-token
  benefit remain untested.

Interpretation: the model exhibits a small deterministic Pareto frontier, not
a universal winner. Central claims reduce more blocked attempts under these
assigned schedules. Local markers help only while visible before the TTL and
avoid the model's explicit central-message counter. NONE remains a zero-message
baseline. No policy changed authority because every arm shared the same atomic
gate; this does not establish that a real UI marker can safely replace or
supplement such a gate.

## Reproducibility

- Preregistration posted before T2 execution: Issue comment `5908396134`.
- Freeze: [`FREEZE.md`](FREEZE.md).
- Source identities: [`SOURCE_MANIFEST.md`](SOURCE_MANIFEST.md).
- Formal receipt and command: [`EXECUTION.md`](EXECUTION.md).
- Raw: [`raw/raw.jsonl`](raw/raw.jsonl), SHA-256
  `1093ab8d5750fe305e22413b470b909badea2e670a57a2d68faaabbe052ac3b4`.
- First audit code/output: [`audit.py`](audit.py) /
  [`AUDIT_V1.json`](AUDIT_V1.json).
- Supplemental audit code/output: [`audit_v2.py`](audit_v2.py) /
  [`AUDIT_V2.json`](AUDIT_V2.json); additional auditor source hash is retained in
  [`AUDIT_V2_MANIFEST.md`](AUDIT_V2_MANIFEST.md).
- Local publication checks, including the sparse-checkout limitation, are in
  [`LOCAL_CI.md`](LOCAL_CI.md); hosted checks are still required.
- T1 STOP, T2 preregistration, and bounded T2 result were all posted to
  [Issue #5346](https://github.com/Unjuno/agent-interface/issues/5346). The
  Issue remains open; no runtime code was changed.
