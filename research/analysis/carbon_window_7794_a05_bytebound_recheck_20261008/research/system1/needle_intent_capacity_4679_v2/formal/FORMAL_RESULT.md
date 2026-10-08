# Formal result — Issue #4778

Allocation `needle-intent-capacity-4679-v2`, branch
`research/needle-intent-capacity-4679-v2-20260927`, frozen source commit
`c215a33c2bd78dfaac960cf47d3fbb0c30eb4446`. The freeze was committed/read back
as `85437f0bed640a2be88e371a3b99f18e5dcaddb5` before the single trainer
invocation. Freeze SHA-256:
`6446941579d1424cbf3391226839416dc6e3ddc4e5e0d3485fe49a5f7ea5c693`.

## Outcome

The one trainer invocation exited 0 and completed all nine fits (three arms ×
three seeds; 900 updates per fit). The frozen first audit exited 2 with
`STOP_AUDIT_INTEGRITY`: it hard-coded the predecessor allocation name and
applied the teacher's raw label-disagreement fraction as a purported control.
No training was repeated. The defect is preserved in `initial-audit/`.

After identifying the audit-only defects, a successor audit source changed
only (1) the expected allocation string from v1 to v2 and (2) the control
predicate to the preregistered state-only exact-intent gate. The synthetic raw
files were not changed. A fresh isolated Docker container audited those raw
files read-only. Its decision was `PASS_INTENT_FIDELITY_NO_CAPACITY_NEEDED`,
with zero audit errors and all 10 mutation controls rejected. This is a
post-hoc corrected analysis, not a clean pass of the originally frozen audit;
the distinction must remain visible in any downstream use.

| Seed | State-only exact-all-intents | Width-24 accuracy / exact / disagree accuracy | Width-64 accuracy / exact / disagree accuracy |
|---:|---:|---:|---:|
| 4153201 | 0.0889 | 0.9747 / 0.9058 / 0.9723 | 0.9806 / 0.9277 / 0.9787 |
| 4153203 | 0.0801 | 0.9730 / 0.9043 / 0.9707 | 0.9835 / 0.9365 / 0.9822 |
| 4153207 | 0.0796 | 0.9779 / 0.9160 / 0.9760 | 0.9786 / 0.9209 / 0.9768 |

Both intent-aware widths cleared every preregistered candidate gate in all
three seeds. State-only failed strongly. Therefore the fresh-seed result does
not support a capacity requirement at width 64 for this synthetic task; width
24 was already sufficient under the frozen gates. The older #4679 result and
this successor remain distinct. Neither supports natural-language skills,
online adaptation, GUI success, real-world safety or product readiness.

## Execution and provenance

- Docker tag before and after: `needle-pilot05:local` →
  `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`
  (`linux/amd64`).
- Limits: one CPU, 2 GiB, 64 PIDs, offline, read-only container root/source,
  bounded tmpfs, no-new-privileges, pull disabled.
- Trainer host: Windows 10 build 26200, Python 3.11.9. Trainer container
  Python 3.12 / Torch; NumPy-unavailable warning did not prevent execution.
- Exactly one formal orchestration. The corrected auditor was a separate,
  explicitly post-hoc, read-only analysis; no fit, seed, threshold or raw was
  changed.
- The frozen preregistration asserted teacher-disagreement fraction ≥0.50 as a
  discriminator, although all arms necessarily share the same teacher labels
  and this fraction was ~0.91–0.92. It was logically vacuous and did not
  discriminate the negative control. The proper discriminator already
  preregistered was the state-only exact-intent accuracy gate ≤0.60. This
  flaw and the initial audit STOP are retained, not erased.

See `EVIDENCE_MANIFEST.json` for byte sizes and SHA-256 identities of every
raw output, initial/post-hoc audit, invocation record, log and freeze artifact.
