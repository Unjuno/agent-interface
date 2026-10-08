# #5172 Stage-0 schedule evidence-contract construction

## H / T / D / C / U

**H.** A raw-only verifier can bind the base optimizer schedule `base_row_indices` to an exact closed digest-key set, independently regenerate the schedule, and reject malformed or inconsistent evidence before any model fit. This directly addresses the missing schedule digest named by the predecessor #4899 formal audit.

**T.** Allocation `needle-role-router-online-lora-audit-v2-20260928-stage0`; source lineage is open Draft PR #4906 head `30c4a4d867484b0f7c9687ee78de9f5a0e71d49c` (not main; preserve its HOLD unchanged). Intake main `ceda253410ce738571580a5980a4e26dc1c3352a`. Use synthetic fixture IDs 17/29/43 (not training seeds), all four registered arm identities, 400 base schedule rows per fixture and 128 per-arm update records. The runner is not imported; no model, optimizer, `fit`, `run_seed`, training seed, output allocation, GPU, Docker, network or GUI is used. Run `python -B -m unittest -v test_stage0.py` in Python 3.12.10. This host-only execution is construction evidence, not the later Docker formal run; #5085 reports shared lane unobservable/occupied and gives no lease.

**D.** `PASS_AUDIT_CONTRACT_CONSTRUCTION_SCOPED` requires one positive fixture covering 3 synthetic seeds × 4 arms, exact base schedule digest coverage, per-arm schedule reconstruction, zero fit/update counters, and rejection of missing/extra digest keys, reordered/duplicated/mutated indices, digest mismatch, noncanonical JSON, duplicate keys, inconsistent arm/seed identity, and nonzero optimizer count. Any baseline rejection or accepted mutation is FAIL_AUDIT_CONTRACT. This gate cannot authorize a later fit.

**C.** Builder and auditor separately implement the deterministic contract schedule; they do not import one another's helpers. Tests mutate deep copies of the positive fixture and use a separately serialized raw copy for the auditor. Exact raw-schedule formulas are synthetic contract sentinels, not a substitute for re-running the predecessor PyTorch trajectory. The Stage-0 suite is executed on host because shared Docker ownership is not cleared; container portability remains untested.

**U.** This is schema/schedule contract construction only. It does not test the predecessor auditor against formal raw, model/optimizer replay, the online LoRA quality hypothesis, the frozen pinned image, Docker behavior, training seeds, or any scientific quality gate. Fresh formal seeds remain unassigned; no fit or retry is performed.

## Frozen implementation

The executed source files are `fixture_builder.py` (SHA-256 `e704492b76b88691f40df1af7afb01fd779a989dc2746869b18c269134169b19`), `raw_auditor.py` (`151def08a9bc77f1a683f5c38f1d2f00352a49001b9c41cff96bc6a7c820a8bb`), and `test_stage0.py` (`5b4ad8346f33f6b02c2147e30ed1c559cd7412a40595a6a725131fbb2a962d06`). `FREEZE.json` SHA-256 is `d6928d856d73977a763395ec4797f32d19847c2923a837bf08ea9cb132b3cb1a`; `FREEZE.sha256` matches it. The frozen builder/auditor/test hashes are verified inside the unit suite.

## Executed result — 2026-09-28

Status: **`PASS_AUDIT_CONTRACT_CONSTRUCTION_SCOPED`**.

- Raw fixture: 14,624 bytes, SHA-256 `0bb775af12795bf812eec1b978a924223c149786267b982f485796abfc60cb71`; it covers three synthetic fixture IDs, all four arms, 1,200 base-schedule rows and 12 arm records. The independently implemented auditor accepted it with `errors=[]`; exit code 0.
- Test command: `python -B -m unittest -v test_stage0.py`; **12/12 passed**, exit code 0. Ten raw-evidence mutations were rejected: missing/extra digest key; reordered, duplicated, or changed index; digest mismatch; noncanonical encoding; duplicate JSON key; inconsistent arm/seed identity; and nonzero optimizer counter.
- Explicit counters: fit invocations 0; optimizer updates 0. The predecessor `runner.py`/`audit.py` were not imported or executed. No formal seeds were used.
- Exact command outputs and the disposition are retained in `RESULT.json` alongside the raw fixture.

No Docker container was launched. The Windows Docker Desktop `desktop-linux` engine responded at version 28.5.1 and its current `docker ps` was empty, but #5085's latest coordination record says the shared OrbStack inventory/ownership is unobservable and there is no exact lane lease. An idle separate engine is not treated as authorization. Therefore this PASS is host-only contract construction and does not establish pinned-image/container portability or authorize Stage 1/formal fit.

## Scope boundary

The schedule sentinels are deterministic contract fixtures, not a replay of the predecessor's PyTorch-generated schedule. No model, optimizer, `fit`, or `run_seed` call occurred. The result does not repair or upgrade #4899's prior `HOLD_AUDIT_INTEGRITY`; it only validates a proposed closed digest-key contract. Fresh formal seeds, source freeze for a corrected full experiment, exclusive CPU/Docker ownership, and a later independent formal audit remain outstanding. Local files were staged under `work/needle_role_router_stage0_5172/`; the source is not integrated until its additive PR is reviewed and merged.
