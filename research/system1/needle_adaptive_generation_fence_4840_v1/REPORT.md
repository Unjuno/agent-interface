# Issue #4840 — post-update generation fence

## H/T/D/C/U

**H.** An adaptive proposal should be eligible only when its captured adapter generation, intent, scope, evidence generation, committed update lineage, calibration, and adapter digest match the currently active validation envelope. After activation or rollback, proposals captured under an old generation must yield. Confidence alone should admit directed stale/invalid examples.

**T.** Frozen allocation `needle-adaptive-generation-fence-4840-v1`, Issue #4840, branch `research/needle-adaptive-generation-fence-4840-v1-20260927`, additive path `research/system1/needle_adaptive_generation_fence_4840_v1/`. Main intake: `a07fa7c1539316d9f951767649c6555d63faf10b`. One 64-row deterministic shadow fixture (8 rows in each of 8 strata), 15 malformed/stale controls, no model training, one Docker study invocation and one separate raw-only auditor invocation. Exact preregistration and source hashes are in `FREEZE.json`; every frozen file was read back from the branch and byte-compared before formal execution.

**D.** Frozen result: **`PASS_GENERATION_FENCE_SCOPED`**.

| Gate | Result |
|---|---:|
| Rows independently checked | 64/64, exact agreement |
| Per-stratum count | 8/8 in each of 8 strata |
| Unsafe eligibility on negative rows | 0/56 |
| False YIELD on current-valid rows | 0/8 |
| Confidence-only negative eligibility | 56/56 (gate >=40) |
| Tamper/stale controls rejected | 15/15 |
| Independent audit errors | 0 |
| Authority grants / training updates | 0 / 0 |

At generation 1, a validated candidate activation is represented; rollback creates a new generation 2 rather than restoring/reusing generation 0 or 1. Old-inflight, delayed-old, pre-rollback replay and future-generation proposals all yield. Current generation 2 proposal remains `ELIGIBLE_PROPOSAL_ONLY`; it is not dispatched and has no authority. Intent/scope/evidence mismatch, non-committed lineage, expired calibration, adapter-digest mismatch and confidence below threshold also yield.

## Execution and provenance

- Docker Desktop CLI/server: 29.8.0 / 29.8.0.
- Cached image: `needle-pilot05:local`, exact ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64.
- Containers: `--pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --security-opt=no-new-privileges`; source read-only. Formal raw was written to a fresh dedicated Docker volume. The independent auditor ran in another container with the raw volume mounted read-only and wrote to a separate audit volume.
- Formal command: `/usr/local/bin/python -B /src/study.py /out/formal_raw.json` (exactly once).
- Audit command: `/usr/local/bin/python -B /src/audit.py /evidence/formal_raw.json 0090e4320e445f1f8fbb9b048e5cde1b1a02ced3650b42fa7918cb6ace1fdc8c` (exactly once).
- Runner SHA-256: `0090e4320e445f1f8fbb9b048e5cde1b1a02ced3650b42fa7918cb6ace1fdc8c`.
- Auditor SHA-256: `e0e9ecbd2316dad0f5b3fb61aae2df7c013e867cc7cbd883590ec32a142fb0bc`.
- Construction tests: 11 passed, zero training. An earlier pre-freeze test attempt failed three assertions because a NaN corruption value could not be encoded by the strict JSON evidence format. The control was changed before freeze to a string-valued confidence; the failed attempt was before any formal call and did not consume a model/training allocation.

Raw payload is 50,864 bytes, retained losslessly as six ordered parts plus `RAW_MANIFEST.json`. SHA-256 of the exact Docker-volume/exported raw bytes: `a683e6920198a5f200bb8f22a5b03f93b90c0d1e82a22cd3ae9203d907d04758`. The runner's canonical payload digest (excluding its digest field/newline) is `c1c9cc3c8a815bc1159315d0968a34e8c8f1c4c7d2a110b554e0a686ecb2319c`. Audit JSON SHA-256: `1cd421de93a381b1a78ee7e646ce42a691e89be51ba73e70b6fc8191f684ec6f`. Formal stdout SHA-256: `c3a85fe9ded05881505c596b3756af132ead1865bf826ecc260d22b73930cf3f`; formal stderr and auditor stderr are empty (empty-file SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). `SUMMARY.json` and `SHA256SUMS.txt` record the artifacts.

## C/U — interpretation and limits

This validates a finite, authored metadata contract and implementation fixture, not a learned model or the repo runtime. The negative rows are directed controls, not estimates of natural stale-proposal frequency. String digests are integrity labels, not signed authenticity. No Astra demonstrations, model behavior, actual online updates, GUI, task effect, concurrent process race, crash durability, latency benefit, action authority, or product/runtime readiness was tested. Promotion is limited to this construction/protocol evidence.
