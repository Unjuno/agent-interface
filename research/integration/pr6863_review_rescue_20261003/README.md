# Rescue of historical compiled-sequence review evidence

Original PR #6883, source `fef3fb8c5e86815839f514b72edb2e785c300060`.
The sibling `pr6863_review_20261003_01a0ff58/` remains an exact 48-file copy,
including its 47-target manifest and original verifier. This qualification is
kept outside it so its strict manifest-coverage check remains meaningful.

Local read-only verification reproduces PASS_SCOPED_REVIEW_PACKAGE with zero
errors: 180 saved rows per source, 26 malformed execute entries at old base
versus zero at old head, and three type-corruption counterexamples falsely
accepted by the original author auditor. The repaired v2 raw-only review
oracle rejects all five corruption controls in both arms. These are logical
fixture dispatch records, not physical input or actual GUI effects.

Original v1 failures, retained-before audit failure, ineffective first oracle
control, publication/export failures, source snapshots and private-path
derivation/custody limits remain unchanged. The proposal JSON digest matches,
but both recorded binary-diff hashes differ from the expected pin. This
historical discrepancy is retained as unresolved, not repaired or called
source corruption. Review feedback is not a committee vote or main application
certificate for the original superseded proposal.

Current promoted compiled_gui.py is not byte-identical to the old reviewed head.
No old snapshot is restored into runtime; no probe/candidate, formal allocation,
native backend, container or original core-suite producer is re-executed.
New tests invoke only the old read-only package verifier and raw-only v2 oracle.
Passing archival integrity does not establish current implementation safety,
concurrency, performance, native input/release, model or task effect.

H/T/D/C/U remains historical finite exact-type callback-boundary evidence;
rescue D is PASS_ARCHIVAL_INTEGRITY_AND_SAVED_REVIEW only. Authored malformed
case counts are not natural prevalence. User authorized rescue of old remote
work and local-first PR integration; ordinary GitHub branch rules apply. No
committee approval or privately retained original evidence is fabricated.
