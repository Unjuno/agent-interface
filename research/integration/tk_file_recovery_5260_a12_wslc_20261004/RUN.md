# A12 first-run ledger

Prospective registrations: #5260 comment 5972891787 and #5085 comment 5972891918.
First result recorded at #5260 comment 5972927818.

- Frozen source: bdab824dc95c637cc8fdf9045cc6996f6cff8bae.
- Freeze SHA256: 7a0c77dd21ac163c08d9fed8fa8bb176ca378b84288c7d686cc25c6b06608a5f.
- Candidate: 2026-10-03T19:56:05.166616Z to 19:56:16.479464Z, 11.3118483 s, exit 0.
- Auditor: 2026-10-03T19:56:27.005552Z to 19:56:27.659781Z, 0.6540700 s, exit 0.
- Candidate raw SHA256: 50dddf0886a74e6b61cf7e7624b1199d80a530d65e7e85e2644e057cef9c4f22.
- Auditor stdout SHA256: 1d0a974bb3cb020521ff8493e3b57cc4a8bfb0a47ec0b5ed013dede120aa8396.
- Formal invocations: candidate once, auditor once; retries zero.
- Verdict: METHOD_PASS_FINITE_FIXTURE_ONLY / H_PASS_FINITE_FIXTURE_ONLY; errors/task_errors empty.

| Index | Mode | Task | Target | Keys | Save | Ordinary file |
|---|---|---|---|---:|---:|---|
| 0 | DRIFT_REFUSE | compact | empty | 0 | 0 | absent |
| 1 | DRIFT_RECOVER | offset | hns | 3 | 1 | exact hns |
| 2 | STABLE | offset | hns | 3 | 1 | exact hns |
| 3 | DRIFT_REFUSE | offset | empty | 0 | 0 | absent |
| 4 | STABLE | compact | hmt | 3 | 1 | exact hmt |
| 5 | DRIFT_RECOVER | compact | hmt | 3 | 1 | exact hmt |

Decoy empty in all six. Exact argv, image identity and source hash map are in
FREEZE and unchanged original receipts. Image pinned, network none, source RO,
auditor input RO, nonroot UID, private Xvfb/Openbox. Scoped processes exited;
peer resources untouched. WSL warning SHA256
2562006e62622bcf41c809d627cdc2c6250516b8cf1c9ccd28072c331fcc4096 retained.

Preparation: 43 Linux tests passed before freeze; Windows 42 passed with one
explicit private-Linux-display skip. PREPARATION.md retains earlier construction
failures; none were formal allocation retries. Post-run verification is additive
and must never relabel or overwrite the first outcome.

Post-run delivery checks: Windows 44 PASS / one explicit Linux-display SKIP
(45 discovered); pinned private Linux container 45/45 PASS, including the
non-formal real-Tk Save construction. Data-only retained reconstruction PASS;
nine copied-record mutation controls rejected. Initial manifest generation
included an accidental blank record and correctly returned FAIL_RETAINED_PACKET
with unsafe_manifest_path; removed only that post-run manifest blank record.
Formal frozen source and all original evidence remained unchanged. This was
not a formal candidate/auditor retry or a relabeling of their first result.
