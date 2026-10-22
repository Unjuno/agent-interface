# Supplemental current-head replay (PR #7429 d355725)

This folder reruns the deterministic post-I/O cancellation composition schedule with ExecutorV12 fetched from PR #7429 head `d35572515f828f458f7bc7406334f74707164199`. The earlier #7473/e22 snapshot and result remain unchanged.

It composes that executor source with pinned #7440 owner v12 and transition-owner v4 sources, plus current-main executor/lease dependencies from `0178fd24e9c317fff40e0fa1952fbe7e8ae01078`. It uses fake Xlib only. This is a source-freshness replay of one forced software interleaving, not physical-release, application/game effect, useful-feedback, bounded-recovery, or live-allocation evidence.

Both arms passed 1/1 on Windows CPython. The raw-only audit reports `PASS_SCOPED_REPRODUCTION` and rejects three corruptions. The executor source, tests, dependencies, and raw output records are retained here; source blob IDs and results are in `SOURCE_MANIFEST.json`.

Run from repository root:
```text
python -B research/live_control/cancel_release_publication_59/late_cancel_composition_v1/current_head_replay_7429_d355/test_postsample_composition.py
python -B research/live_control/cancel_release_publication_59/late_cancel_composition_v1/current_head_replay_7429_d355/test_ordinary_release_control.py
python -B research/live_control/cancel_release_publication_59/late_cancel_composition_v1/current_head_replay_7429_d355/audit_pair.py
```
