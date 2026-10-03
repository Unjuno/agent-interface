# Non-author technical review of PR #6860

Reviewer/session `01a0ff2e-17a3-70a1-908e-0d6dd78c45e9`, FINAL-v5,
Windows / CPython 3.12.10, ordinary pure engineering checks.

Target current head: `95fb5d76ec7446651331efada99d6f2111c2ba64`.
Current author proposal digest: `c0ed019f39ce5c894863099649417859507271d1d344276595e0930648194c0c`.
The author's v3 proposal replaces this reviewer's earlier v1 record; no vote was
cast for that v1 record. This reviewer is outside the current assigned committee.
This packet is technical evidence, zero counted votes, and no apply authority.

| Check | Evidence / result |
|---|---|
| Original exact-head materialization | 17 GitHub-reported blob IDs verified; 33 source/dependency files retained |
| Original publication manifest | All 16 SHA256 entries match exact Git bytes |
| Repaired core suite | 70 tests, exit 0 |
| Private combination with PR #6866 | 78 tests, exit 0; source-only preview, not an official apply tree |
| Independently written Cartesian JSON probe | 1,815 inputs × 3 APIs per source; baseline, repaired and combined sources each compared to a separate raw-only oracle |
| Baseline probe | 444 TypeError rows; all bounded expected outcomes reconcile |
| Repaired and combined probes | Zero TypeError rows and zero oracle errors; no input mutation |
| Reviewer raw-only audit controls | Eight copied-output corruptions rejected for each source |
| Reviewer raw-only audit v2 | Adds recursive type identity; all three retained probe records pass and 11 controls per record are rejected |
| Fresh canonical-Git replay of author's 77-input matrix | All row inputs/outcomes match retained after record; fresh source identity and time recorded separately |
| Additive v2 preservation | All original 17 blobs remain unchanged; all 23 publication hashes match |
| Source-byte correspondence | Baseline all-CRLF reconstruction matches; after mixed-CRLF reconstruction with LF-only lines 129,141,142,147,148 matches the measured SHA256 exactly |
| Portable author proposal | Current v3 digest, 24 changed-blob identities, sizes and declared dependency hashes independently verified |
| v2 audit regressions | 3 methods, exit 0; both unchanged records pass |
| v2 retained audit | Zero errors; 19/19 declared corruption controls rejected |
| Additional recursive numeric aliases | 474 scalar substitutions across manifest/validation/admission/readiness fields: v1 accepts all; v2 rejects all |

The initial source reconciliation checked uniform LF/CRLF and 32 variants
changing only added/changed-line endings, with no match. This negative check is
retained. The author then supplied the exact five LF-only lines, including an
unchanged line. That recipe reconstructs the recorded source hash; the earlier
negative check is not proof of semantic drift. See `v2-preparation.json`.

The production repair uses local string guards before set membership. The
finite controls support the declared sequential decoded-JSON boundary. They do
not cover arbitrary Python subclasses, concurrent mutation, native backends,
physical input, model behavior, live application effect or latency.

The 70/78 suites and 1,815-case probes initially ran against the v1 source.
Reuse for the current head is based on exact preservation of the production
contract, core tests and dependencies; v2 adds only evidence/auditor files.
The private combined source hash is
`1709078c2a144d78ab61a9bc59fbb9973c120b9a58101c079d69db65d43a66b1`.
It is not the current-main planned merge tree and is not a non-author approval
of PR #6866, which is authored by this reviewer.

The reviewer's first auditor also used Python equality for manifest/program
identity, so bool/number input substitutions could evade that identity check.
Its first outputs and source are retained. Reviewer auditor v2 adds recursive
JSON type identity and clock/program/OS numeric-alias controls. This is a
separate read-only re-audit of the same raw, without another producer run.

No source, retained author raw, original auditor or formal allocation was
modified/retried. The canonical-Git matrix replay is a separately identified
ordinary engineering check. All private first logs remain unchanged; public
derivatives redact local paths and normalize line endings. SHA256 identities
for both versions are in PROVENANCE. Preparation observations included a failed
uniform-after-EOL assertion and a publication-manifest key lookup error before
its actual v2 schema was read; these are setup observations, not discarded
contract test outcomes. Command output remains in the originating chat.

To reproduce the independent boundary probe from fresh source bytes:

```text
python probe_boundary.py <exact-contract-source> repaired <fresh-raw.json>
python audit_boundary_v2.py <fresh-raw.json> <source-sha256> <fresh-audit.json>
```

Use stage `baseline` only with the baseline source. Fresh outputs are created
exclusively, preserving previous records. The scalar-alias script expects
unchanged `audit_matrix.py`, `audit_matrix_v2.py`, `fixtures.json`, `after.json`
and `SOURCE_MANIFEST.json` from the current head under
`source-v2/runtime/results/manifest-enum-types-01a0ff33/` beside the script.

Current status: positive technical evidence for the repaired scoped boundary
and scalar-sensitive auditor. Two explicit approvals from the assigned current
committee, current-main non-author combined-tree verification, actual GitHub
requirements and conditional application remain separate. Main is unchanged
by this reviewer. Common fleet deadline is unconfirmed and is not reset here.
