# Observed read receipts versus broad dependency token — retained result

Task `COORD-OBSERVED-READ-RECEIPTS-20260916-018`, Issue #501. Publication base `e2f3afadef75f8778a4e9f07b51f7c9329b23c76`; source-first freeze head `5aeba7e6f8c1615a9c6bc367f195a27b279aaa76`.

## Decision

**`PASS_OBSERVED_READ_RECEIPTS_SCOPED`.**

The effect owner checks token revisions and commits generation in one SQLite `BEGIN IMMEDIATE` transaction. The only changed factor is dependency-set provenance: a broad authored token includes A/B/U; the observed token is generated from the decision's actual A/B reads.

| policy | scenario | token keys | commit | ground truth |
|---|---|---|---|---|
| broad | stable | A,B,U | yes | correct |
| observed | stable | A,B | yes | correct |
| broad | A changes | A,B,U | no | correct |
| observed | A changes | A,B | no | correct |
| broad | unrelated U changes | A,B,U | no | **false contention** |
| observed | unrelated U changes | A,B | yes | correct |

Observed-read policy is ground-truth correct **3/3**. Broad policy is correct **2/3** and produces exactly one preregistered false contention when only U changes. Both policies reject the relevant A revision change before generation effect. Every successful transition writes generation=2 exactly once; rejected cases retain generation=1 with zero generation events.

Frozen independent audit: `PASS_OBSERVED_READ_RECEIPTS_SCOPED`, errors 0. Four copied-evidence corruption controls reject 4/4: committed-label flip, injected unrelated token receipt, deleted generation event, and duplicate case id. Formal measured-ID reruns: 0.

## Interpretation

Observed read receipts can provide a narrower transition dependency token than a broad authored state snapshot when all task-relevant reads flow through the receipt-producing accessor. This transfers the `all and only invalidating state` principle from #487 from an authored dependency set to an execution-observed set.

The result does **not** prove automatic completeness. An uninstrumented/bypassed read can be task-relevant while absent from the token. That is the next single discriminator.

## Retention

Full deterministic evidence archive `observed_read_receipts_v1_evidence.tar.xz`: 6,316 bytes, SHA-256 `26115b11e1c025ff25f74fff7bcd2613fc4eeb720bbbb53cbe904dcef6eccd5d`; internal manifest SHA-256 `80d27d8e808296f47b4ff57e3ac3927554e7599db5994aa96a167d4c2973c08b`. GitHub retains the archive as Base64 plus a SHA-verifying reconstruction script, exact formal result/audit, source, plan and corruption controls.

## Limits / next question

Cooperative local SQLite and one authored decision only. No arbitrary-code dependency discovery, uninstrumented reads, multi-writer concurrency outside the transaction, crash/power-loss or distributed claims. Next rung: keep the same owner/token mechanism but make B task-relevant through one deliberate uninstrumented bypass read; test that a B change becomes an unsafe stale commit unless the access discipline itself is enforced.
