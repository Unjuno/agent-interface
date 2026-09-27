# Corrected #4447 control-map audit — successor #4511

Issue: #4534. Allocation: `temporal-resume-audit-control-map-20260927-01`.

## Lineage and immutable inputs

Preserve #4447's first outcome (`HOLD_AUDIT_CONTROL_CANDIDATE_RETURN_CODE`) and #4511's frozen rev02 verifier/outcome (`HOLD_GATE_CONTROL_DENOMINATOR`). This follow-up re-audits copied evidence only; it does not replace either result or rerun the 54 temporal cases.

Read only:
- #4447 evidence commit `de1064b335a6567c57817209485cf18d25d9e3f2`, manifest SHA-256 `1584edb3a45202b3e816d2a9735708265dae279fd4e18d8680fded7756cc3855`.
- #4511 frozen source commit `3a5557245fd1f57e9d65e9ddfd732d67abd41b69`; `verify_receipts.py` SHA-256 `a5fa59f118c46d2c01b555b32dbc3af57d80b2e0df1eea55961ef5ad994faac2`.
- Canonical #4447 source capsule rehydrated from exact blobs; 14 source-manifest entries, fixture SHA-256 `5531e1296e31064da7661138f6ae9036e473b5c953ebd82b3f1ce28a9409fd61`, schedule SHA-256 `90c2d136dfe7e429bfdc504c12fff51e4ad141030080b897d11249a5f28151cd`.

## H / T / D / C / U

**H:** #4511's `control_accept` used BATCH5 row 0 (case 45), whose candidate status was already `OK`; it was a no-op and did not reproduce the tenth original #4447 corruption mutation. The original #4447 control targets case 48 (BATCH5 row index 3), a `foreign_epoch` refusal case, and changes its candidate status to `OK`. The #4511 auditor should reject this correctly targeted corruption while continuing to reject child process receipt mutations.

**T:** First validate exact case identity, not a magic row position. Then freeze a schedule with 12 copies of retained evidence: the ten original #4447 mutations (including the corrected case-48 `control_accept` and the candidate return-code control), one added comparator-returncode mutation, and one separate unchanged positive acceptance control. Reconcile duplicated JSON/stdout fields and rehash each mutated copy manifest. Run the unchanged baseline verifier and all copies once inside local Docker Desktop, network disabled and read-only except bounded scratch/output. The source capsule, #4447 evidence, and #4511 verifier are read-only mounts. No GitHub Actions, model, GUI, network experiment, or temporal-case execution.

**D:** `PASS_CONTROL_MAP_AUDIT_SCOPED` only if baseline independently reports 54 rows, candidate 48, six corruption refusals, >0 comparator disagreements and no errors; all 11 byte-changing mutations are rejected; the unchanged acceptance control remains byte-identical and is accepted; all temporary copies are removed; and original source/evidence hashes match before/after. Otherwise retain HOLD/FAIL/STOP; no source or gate tuning after outcome.

**C:** Same-author, deterministic, offline copied-evidence verifier audit. The controls are targeted robustness checks, not prevalence estimates or independent review.

**U:** Does not rerun or upgrade #4447's scientific result, resolve predecessor fixture provenance or container-kernel equivalence, or establish production behavior, durability or performance.

## Execution order

Read historical mutation identity -> freeze this plan, runner, tests and input hashes -> GitHub-read back exact freeze -> synthetic-only Docker construction checks -> one formal local Docker run -> preserve all receipts and independent hash/denominator audit -> additive evidence PR. If a source preflight fails, stop before the formal verifier. If the formal run occurs, do not rerun it or tune gates.
