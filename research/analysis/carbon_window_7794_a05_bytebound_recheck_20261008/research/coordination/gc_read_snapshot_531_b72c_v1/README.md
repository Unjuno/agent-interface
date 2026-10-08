# b72c read-snapshot evidence — retrospective delivery

Publication date: 2026-09-25. Delivery owner: Issue #4370.
Intake main: `4a1f3957e91b412a64769199f78f2c4b0102d28b`.

**This publishes a completed, locally frozen experiment. New formal/GUI/model
invocations in this continuation: 0.** The original `REPORT.md`, `PREREG.md`,
`FREEZE.json`, sources and observations remain byte-identical. Their historical
GitHub-write-unavailable statements describe the original session, not this
later delivery. GitHub registration is retrospective, not public preregistration.

## Retained result and integration constraint

Original allocation: `gc-read-snapshot-531-b72c-20260922-01`.
Decision: `PASS_GC_READ_SNAPSHOT_BOUNDARY_SCOPED`.

| Reader | Cases | Mixed states | Rebound-old proposals | Genuine-next refusals |
|---|---:|---:|---:|---:|
| AUTOCOMMIT, separate completed SELECTs | 20 | 4 | 2 | 2 |
| SNAPSHOT, one read transaction | 20 | 0 | 0 | 0 |

Forty cases produced 120 **read-only classifications**, not 120 task actions.
The exact unchanged old request was never admitted as new. Only a changed-content
old-ID diagnostic proposal exposed the acceptance difference. The two mixed
history-first observations did not change these particular classifications.

An atomic retirement writer does not make separate reader transactions one
snapshot. Restore history, retirement marker and generation consistently.
However, eight SNAPSHOT observations remained coherent **historical** views after
the writer committed. Coherence is not latest-at-return or input authority.
BEGIN DEFERRED also does not establish a data snapshot before its first read.

This constrains the result/recovery composition under #24/#2084/#2789 and supplies
the primary evidence referenced by #4063. It changes no production runtime or
admission rule, does not diagnose a current production defect, and closes no
parent or global ROADMAP gate. #3929/#4037/#4063/#4086 retain their separate scopes.

## H / T / D / C / U

- **H:** atomic history retirement can be reconstructed inconsistently by split
  reads; a single read transaction prevents the selected mixed views.
- **T:** two policies, two read orders, five barrier-selected writer placements,
  two repetitions; 40 cases, 80 actual actors, four fixed ten-case batches. Original
  Linux execution container, CPython 3.13.5, SQLite 3.46.1 WAL, no Docker/OrbStack
  image attestation. Exact #531 model blob
  `24329aaedf166b98a5babf5cfb9c61af7c6f40f0` is unchanged.
- **D:** original 40/120 source/database/process audit passes, all 12 evidence
  mutations reject, all 10 unit methods pass. No original rerun, replacement,
  exclusion or post-freeze source tuning. Complete gates and field/unit table
  are in the original report and preregistration.
- **C:** cooperative research adapter and trusted scope. The writer retires a
  fixed prefix without concurrently accepting new work. Downstream current
  admission may reject a stale proposal; no such guard was bypassed or tested.
- **U:** no GUI effects, model recovery quality, timing/token benefit, power loss,
  multiple writers, issuer restart, authentication, general reliability or product
  acceptance. Separate audit implementation/process has the same author, not an
  independent human reviewer. Timestamps are diagnostic, not calibrated metrology.

## Exact evidence inclusion and explicit ancestor exclusion

The original complete conversation archive is 209,964 bytes, SHA-256
`9439064827c483529e86260149bfedefc38f3e6201dfaed70ce1544c129a63c9`,
containing 918 files. It remains unchanged.

This repository capsule contains **917 primary-study files / 9,602,807 bytes**:
all b72c formal and construction data, source versions, failed construction-auditor
control, original manifest, logs, exit receipts, report, preregistration and audit.
Its 80,776-byte XZ archive has SHA-256
`074fde64ac7c6d28ec16e31fe32b69dc1391613e9039b49b45bb8a9da2eb0f87`.

**Exactly one separate ancestor archive is not duplicated here:**
`PREDECESSOR_A61E.tar.xz`, 104,924 bytes, SHA-256
`fc406d0cbdf58fc46dc6fd0f7620bb3315c9d29ac0ec3fba0313745e4a7b6a65`.
It is still in the complete original conversation archive. No b72c source,
observation or failure is excluded. Statements in the preserved old report about
including that ancestor refer to the original 918-file archive, not this capsule.
Do not claim the entire original archive or the full a61e experiment is hosted
by this publication.

The original manifest is unchanged. The restorer verifies its exact digest,
916 included entries, itself, and exactly the one declared omitted ancestor.
Consequently, an unqualified `sha256sum`-style check expecting the ancestor would
fail; use the explicit inclusion-aware restorer below rather than suppressing
arbitrary missing-file errors.

## Read-only reproduction

Run from this published directory, using absent output paths and ordinary Python
3.13 with its standard library. The restorer executes no archived study code:

```sh
python -B test_restore.py
python -B restore.py --out /tmp/b72c-review-4370
cd /tmp/b72c-review-4370
python -B audit.py --controls > /tmp/b72c-review-audit-4370.json
cmp AUDIT.json /tmp/b72c-review-audit-4370.json
python -B test_contract.py
```

Do not use Python optimization flags. Do not run the consumed actor/runner/formal
commands. `actor.py` and `audit.py` are directly readable for review; their bytes
must match the capsule. All remaining original sources, including `vendor531.py`,
are restored without executing them.

The new decoder binds exact fragment order/size/digests, bounded XZ/tar expansion,
regular canonical relative paths, original manifest membership and the six readable
source/report copies. It refuses an existing destination. Its filesystem safety
assumes a quiescent private destination parent, not an adversarial local filesystem.
Hashes establish retained-byte integrity, not author authentication.

## Validation and completion boundary

`REVALIDATION.json` records the fresh original-archive audit and ten unit methods.
`PUBLICATION_VALIDATION.json` records fresh capsule restoration, ten decoder tests,
byte-identical re-audit and unchanged originals. All seven uploaded binary Git
object IDs matched local computation before tree publication. These are local and
remote-byte checks, not repository-wide tests or external approval.

The delivery sequence is original-byte verification -> capsule/source publication
-> exact Git-tree readback -> evidence PR -> applicable exact-head checks/review
-> permitted merge -> main readback. Only the delivery Issue may close. Branch
cleanup requires verified merge, no dependent PR and an available deletion action;
no unrelated branch is changed.
