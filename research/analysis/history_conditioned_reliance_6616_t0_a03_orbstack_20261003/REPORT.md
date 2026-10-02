# Issue #6616 A03 — construction mechanics pass, reviewer hold

## Result

The one-shot OrbStack candidate generated 36 synthetic stimuli and two blinded reviewer packets. The separately executed raw-only auditor independently reconstructed all 36 unique rows, confirmed the equal prior-history multiset and full probe × history × display-arm crossing, verified the oracle was not visible to candidate/reviewer packets, and rejected all four preregistered corruptions. The bounded result is `PASS_CONSTRUCTION_MECHANICS_HOLD_INDEPENDENT_REVIEWER_SIGNOFF`.

The allocation-level decision is `HOLD_INDEPENDENT_REVIEWER_SIGNOFF`: neither of the two independent human reviewer signoffs was collected. This does not satisfy Issue #6616's complete T0 gate. No participants or human responses were involved; no claim is made about reliance, trust, history effects, fatigue, task learning, GUI behavior, user benefit, or product readiness.

## Frozen experiment and execution

Allocation `history-conditioned-reliance-6616-t0-a03-20261003`; preregistered at [Issue #6616 A03 comment](https://github.com/Unjuno/agent-interface/issues/6616#issuecomment-5960846128), with a pre-run source-visibility correction at [the superseding-freeze comment](https://github.com/Unjuno/agent-interface/issues/6616#issuecomment-5960887101). Executed freeze SHA-256 is recorded in `FREEZE.json` and `RUN_RECORD.md`. The design is four equal-multiset histories × three fixed current probes × three presentation arms (36 cells), with candidate and auditor executed once each, zero retries.

The experiment ran in OrbStack VM `research-6680-a01-20261003` using a digest-pinned Python `linux/arm64` image and separate Docker Engine. Candidate and auditor source mounts were disjoint: candidate could not access `oracle.json` or `audit.py`; oracle was mounted only into the auditor. Both containers used `--network none`, 0.25 CPU, 256 MiB memory/swap, 32 PIDs, read-only root/source mounts, UID/GID 1000, all capabilities dropped, and `no-new-privileges`. This does not establish VM-level network isolation.

Candidate and auditor exited 0 without OOM. The audit reports 36 unique rows, equal history multisets, matched current probe crossing, and all four mutation controls rejected. Exact receipts, timestamps, commands, Docker configurations, output hashes, and retained raw outputs are included alongside this report.

## Evidence and limits

- `candidate.raw.json`: raw candidate stimulus rows and execution receipt; 36 rows.
- `reviewer_packets.json`: two differently ordered packets, unsigned.
- `audit.json`: independent reconstruction and mutation-control results.
- `CONTAINER_RECEIPTS.json`: container IDs, exact argv/environment, exit/timing, limits and mounts.
- `RUN_RECORD.md`, `FREEZE.json`, `FORMAL_COMMANDS.md`: lifecycle and source/environment contract.

No response or reviewer signoff was manufactured from packet generation. A future reviewer must independently complete `REVIEW_PROTOCOL.md`; only then may the Issue-level T0 gate be reassessed. Any T1 participant study remains separately unapproved and out of scope.

## Local validation

The A03 contract suite passed 6/6, Python byte-compilation passed, every entry in `SHA256SUMS` verified, the analysis index passed with 572 retained directories, and the research workspace index passed with 156 directories (including strict `--git-tree`). The additive A03 GitHub Actions workflow parsed locally and runs the retained hashes, six contract tests, and analysis index. Other test suites listed in the existing analysis-index workflow passed locally. Two geometry-feasibility tests are tied to that workflow's first CI step restoring historical workflow source SHA `b19000e027e7379ef6c0122e3f8cfd0b2faacb4c54d985ab87d27c1be914f7c2`; when invoked directly against the current checkout, they fail that frozen-file hash assertion. The restore source commit `e2e434dd07e1034c5c4303982a0b1ec33ea35cfd` was independently verified to yield the expected hash. The shared workflow was not changed, preserving the historical source contract.
