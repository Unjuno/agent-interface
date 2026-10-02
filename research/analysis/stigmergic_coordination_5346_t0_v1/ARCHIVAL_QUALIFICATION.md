# Archival qualification: Issue #5346 T0 construction chronology STOP

Date: 2026-10-01. This is an additive archive of already-published source and
host-construction evidence, not a new experiment or a repaired result.

## Original identity and retained outcome

- Source PR: [#5365](https://github.com/Unjuno/agent-interface/pull/5365)
- Exact source head: `80e73fb2a962a4a92d048b8b87051ba276763569`
- Original branch: `research/stigmergic-coordination-5346-t0-20260930`
- Original package tree: `8a232ee2424332ae5faf5c7362e344d34f0e044b`
- Allocation: `stigmergic-coordination-5346-t0-20260930-01`
- Preserved original files: 11 blobs, 86,873 bytes, all at their original paths
  and mode `100644`; no original file is edited or deleted
- Retained raw: `results/construction-host-01/raw.json`, 52,389 bytes,
  SHA-256 `75b135aac6d67168ac31c9d727fc5a7052bd88fc75b8bf7221a98f85f63b6461`

The controlling disposition is the owner's pre-formal construction/model-audit
STOP, recorded after the host smoke in
[Issue #5346](https://github.com/Unjuno/agent-interface/issues/5346#issuecomment-5908559047)
and [PR #5365](https://github.com/Unjuno/agent-interface/pull/5365#issuecomment-5908562142).
The owner stopped v1 before container execution because its candidate and auditor
did not preserve/check the intended recovery chronology. Formal container runner
and auditor invocations remain zero. Do not execute the archived command file,
reuse the withdrawn request, or treat this archive as an allocation or lease.

## Historical claims and their limits

The original package reports 15/15 host tests, 27 synthetic cells
and `PASS_READONLY` with zero reported errors. Those historical strings are
preserved, not promoted: the later STOP controls their interpretation. No source,
tests, runner, auditor or container was executed for this archival preservation.

In `external_mutation / NO_COORDINATION`, the retained event list places worker
1's tick-4 observation before worker 0's tick-2 refusal/re-observation/regrant;
worker 1 then receives B at tick 5 without a new observation after the relevant
release boundary identified by the owner. In `owner_crash / NO_COORDINATION`,
A and B grants occur at ticks 4 and 7 but both effect confirmations are stamped
tick 10. The original auditor checks summary counts and selected event presence,
not the missing per-target chronology constraints. These defects remain intact.
The recorded policy aggregates are not scientific evidence for or against
stigmergic coordination.

The published package contains the raw JSON and a Markdown record quoting the
runner/auditor stdout. It does not contain separate original stdout/stderr,
process exit receipts, a standalone machine audit-output file, or formal
container evidence. No missing process observation or audit artifact has been
reconstructed. Host test and audit claims remain historical reports.

Static byte checks matched all 11 Git blob IDs, the raw SHA-256, all five
`source_sha256` entries, both `protocol_sha256` entries and `FREEZE.sha256`.
One frozen metadata inconsistency remains: `prior_execution.plan_sha256` says
`506cf5b908df13b7124b638e7471209710d3aa1259261e02d6976f002e05c154`, while the
retained `PLAN.md` hashes to
`25af8c9ecacf142363f4db280d2446182067e4c9378aa21fe23b7f4f6299a525`, matching
`protocol_sha256.PLAN.md`. Neither field nor the original plan is repaired here.

The model is hand-specified logical ticks for two workers/two targets and nine
schedules. Local marker publish/observe events and central request/grant
messages are different accounting units. No real workers, live interface,
wall-clock/token benefit, model/GPU result, runtime authority or product/safety
claim follows from this archive.

## Ownership and distinct successors

[Issue #5346 remains open](https://github.com/Unjuno/agent-interface/issues/5346).
This archive does not change its owner, broader research question or future
allocation gates. The separate T1 STOP and T2 scoped finite-model result were
merged through [#5382](https://github.com/Unjuno/agent-interface/pull/5382), merge
`0154e7533fb76a67578e0b2789aa42c32a511369`; that PR explicitly says it did not
modify or supersede #5365's distinct T0 allocation. Their bytes and dispositions
are unchanged. The owner's
[later reconciliation](https://github.com/Unjuno/agent-interface/issues/5346#issuecomment-5908918627)
also preserves the predecessor STOPs.

Original wording about an awaiting formal slot or pending execution is historical
pre-STOP text. Administrative archival delivery cannot authorize that execution,
erase the STOP, establish a new PASS, or close the scientific Issue. The source
branch remains retained; this archive itself does not change source PR status.

## Exact original manifest

Paths below are relative to this package. The new qualification is separate
from this manifest of original published files.

| Original path | Bytes | Git blob ID |
|---|---:|---|
| `CONSTRUCTION_HOST_01.md` | 1714 | `c6201a65d3b84949ada1ac096c174cedaf31d84e` |
| `CONTAINER_COMMANDS.md` | 1977 | `8ea1c200d83fb693e10fd5e7fa211d537e028d95` |
| `FREEZE.json` | 2597 | `1787fc61259c4b297f33ba5e2e27f38b9b12af1f` |
| `FREEZE.sha256` | 78 | `bc3706d41d6e56e981c26815f2a8f659f317d9bb` |
| `PLAN.md` | 4755 | `0a22d6a5a66a2fd236c041b82204d8066a6a03ec` |
| `audit.py` | 5933 | `02dedbc14e1a9a299ea635d0aafbaaa51b295808` |
| `candidate.py` | 11457 | `9ab3fe1b7033926373fdb1e7338619a4b881bd0a` |
| `results/construction-host-01/raw.json` | 52389 | `3dc923e3df6cedd873b86b111a66d7590b3268a4` |
| `run.py` | 866 | `334c2c16120ff265045816fe47092d834f39fdac` |
| `test_audit.py` | 1919 | `b06a4d247c9753168ad7a720e21285dd9ecc706c` |
| `test_candidate.py` | 3188 | `e60f2786a2d03a10073a3dcf9b6235b523394819` |
