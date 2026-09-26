# Raw process-receipt auditor successor — #4447

Issue: #4511. Allocation: `temporal-resume-audit-returncode-20260927-01`.

## Lineage / ownership

This verifies copied retained evidence from #4447; it does not rerun or replace its consumed 54 scientific cases, and cannot upgrade the original HOLD. Preserve #4447 and its raw artifacts unchanged.

Own only branch `research/temporal-resume-audit-returncode-20260927-r1` and additive path `research/integration/temporal_stream_resume_audit_r1_v1/**`. The verifier reads the source capsule and formal-01 data from #4447 commit `de1064b335a6567c57817209485cf18d25d9e3f2` read-only.

Pinned inputs:
- #4447 formal artifact manifest SHA-256: `1584edb3a45202b3e816d2a9735708265da279fd4e18d8680fded7756cc3855`
- source fixture SHA-256: `5531e1296e31064da7661138f6ae9036e473b5c953ebd82b3f1ce28a9409fd61`
- source schedule SHA-256: `90c2d136dfe7e429bfdc504c12fff51e4ad141030080b897d11249a5f28151cd`
- frozen #4447 auditor SHA-256: `41f2500217bd7ea056494d0d9fe747f2131365d7ee64de2ae5b4da710de511af`

## H / T / D / C / U

**H:** The #4447 raw auditor accepts copied evidence whose nested candidate child return code is changed from 0 to 9. A verifier suitable for evidence admission must bind each child return code to the expected first-outcome status, reconcile nested stdout with parsed JSON, and reject that mutation and equivalent prepare/comparator receipt mutations.

**T:** Run the successor verifier against the unchanged 54-case corpus, six raw batches and source schedule/fixtures. Independently recompute the three temporal-policy suffixes for all 48 normal cutpoints; check six refusal cases; reconcile each outer case and child process return code/stdout/parsed receipt; check authority fields and checkpoint-prefix hashes. Then make eleven byte-distinct temporary copies: the ten #4447 evidence mutations plus a comparator-child return-code mutation. Update each copy's SHA-256 manifest and all duplicated serialized stdout/parsed representations so the tests exercise semantic receipt validation rather than stale-hash detection. Invoke the verifier once per copy. No source, original evidence, GitHub workflow, network, GUI/X11, model or task input is involved.

**D:** `PASS_PROCESS_RECEIPT_AUDIT_SCOPED` only if the untouched corpus independently yields 54 rows, candidate 48/48, comparator disagreements >0, six corruption refusals and authority-neutral receipts; all child return codes reconcile; all 11 copied-evidence mutations change bytes and are rejected; the original evidence tree's before/after hash is identical; each copied manifest and final report hash is retained. Any undetected mutation or baseline mismatch is FAIL/HOLD. This does not change #4447's HOLD.

**C:** Same-author offline evidence verification over one deterministic retained corpus, not a new scientific trial or external human review. Mutations are targeted verifier controls, not natural-data prevalence estimates.

**U:** This cannot prove fixture byte identity with unavailable predecessor #4220/#4433 archives, Docker kernel/glibc equivalence, durability, production behavior, or performance.

## Execution sequence

Source/unit construction -> source and decision-gate freeze/readback -> one local Docker verification using the frozen Python 3.13.5 linux/amd64 image with `--pull=never --network none` -> retain baseline audit and all 11 mutation outcomes -> hash/readback -> additive evidence PR. No GitHub Actions scientific run and no #4447 batch rerun.

Construction incident before freeze: the first synthetic-unit launcher failed at import because Python `-I` excludes the script directory from `sys.path`. It read no #4447 evidence and consumed no formal case. The failure is retained in `CONSTRUCTION01.log`; both test and control launchers now insert their own script directory explicitly.

The next synthetic-only run had 3/4 tests pass; its exact-80ms test expected the strict-time policy to remain pending. Inspection of the frozen contract shows strict-time accepts `tick > anchor_tick`, so equality at the deadline is satisfied. The test expectation (not the verifier policy) was corrected and the failure is retained in `CONSTRUCTION02.log`.

After those corrections, the Docker-only synthetic suite passed 5/5 tests (`CONSTRUCTION03.log`). It covered same-tick policy distinction, exact-80ms behavior, nonzero child-exit rejection, stdout/parsed reconciliation and the eleven-control schedule. No #4447 evidence was mounted in any construction run.
