# Recovery review and historical-audit limitation

## Retention provenance

This additive review was prepared on 2026-09-30 for [PR #4878](https://github.com/Unjuno/agent-interface/pull/4878), Issue #4695. The original four files are retained without edits from commit `46db369776d9d85156ac38fa66405822057d05f5` on `research/arena-v1-recovery-boundary-4695-20260927`. All four paths were absent from recovery intake main `7b0f33493506521de10f292c960e9848d81c09d7`.

- `README.md`: Git blob `b7bd2670eb0d05d05ffeaf78de2860dfc40a975e`
- `RESULT.json`: Git blob `fd4a50b7b5f0586fd41bdaad415ad25a1ee7797a`
- `audit_probe.py`: Git blob `12ea2caf0eac78b30f698d6908e53c34da27039b`
- `recovery_probe.py`: Git blob `da8db99f3b2d56aa61c4d1b5bd108ea144c4fbc4`

Static byte verification matches all four Git blob identities. The SHA-256 identities of both Python files also match the values recorded in `RESULT.json`.

## What the retained auditor actually does

The original README, PR description, and result record report a successful independent/raw-only audit. Static inspection identifies a narrower boundary: `audit_probe.py` imports `rows` from `recovery_probe.py`; the imported module has a top-level loop that creates benchmark sessions and runs all five synthetic scenarios. Calling that auditor therefore generates and checks new rows rather than consuming an immutable historical raw file. It must not be treated as a raw-only replay command.

The four-file retained package contains summary counts in `RESULT.json`, not the original five per-seed raw rows or process transcripts. It therefore cannot establish an independent audit of the historical invocation from the published artifacts alone. Matching source hashes does not recover missing outputs or process-exit evidence. The historical PASS label and 14/14 unit-test claim remain unmodified author reports; this recovery does not independently certify them.

## Disposition and limits

Retain the original source, summary, and their limitations as an incomplete historical construction record. No probe, imported auditor, benchmark scenario, Docker container, model, GPU, or formal allocation was run during this recovery; verification was limited to bytes and static syntax/structure. No historical raw was regenerated, substituted, or inferred.

If exact original raw/transcript artifacts become available, add them with their provenance and use a separately reviewed raw-only verification path. Do not rerun the old probe to fill the historical evidence gap. Issue #4695 remains open for its distinct benchmark acceptance, paired evaluation, generalization, and transfer requirements. This retention is not a new scientific PASS, benchmark promotion, or runtime change.

