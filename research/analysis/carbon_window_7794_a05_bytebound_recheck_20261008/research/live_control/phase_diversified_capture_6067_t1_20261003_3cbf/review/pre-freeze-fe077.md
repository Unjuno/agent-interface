# Independent pre-formal review

Reviewer: Popper, agent 01a10170-dbc9-7161-9b2c-5a9dc4e393c2.
Reviewed e2fbed6ef22e091a89c5f21590eb77634c08abf0 and
fe077ca19ff7032a63de866dc60bef85b06f6eb3, read-only.
Disposition: HOLD before source freeze, formal 0/0.

Verified defects:

1. Per-cue chronology did not enforce serial XSync source order. Extending
   cue1 clear completion to +900ms while cue2 drew at +132.001ms let a
   cue1 pixel at +845.003ms change misses8 to7 with false_positives0.
2. Journal parsing and Python equality accepted frame index false versus0,
   and lacked duplicate/nonfinite rejection. The mutated 114-cell stream
   received PASS_TRANSFER_SCOPED.
3. Conditional substituted-fixture weakness: three fixed pulse cells without
   controls/diversified arms could pass. Frozen fixture digest and source
   receipt validation were required; the new oracle also independently
   reconstructs the entire ordered plan.
4. Additional reproduced boundary: the final native/extraction interval could
   extend beyond the declared observation window. It is now gated before
   formal execution; this is not an after-result criterion change.

Checks completed by reviewer: e2f10/10 and fe07712/12 pure tests; timer statistics;
retained native01 first STOP and native02 dark/persistent raw hashes/stream joins.
Native02 maximum capture lateness .241047/.724076ms, child exits0/0/0.
An independently constructed ideal record exercised114cells/912frames and
produced all-miss counts30/14/12. These are synthetic code-check expectations,
not acquired evidence and not to be reported as experiment outcomes.

Design coherent only for the three declared deterministic schedules at equal
eight-frame budgets, not random-cycle population, task or safety outcomes.
Unreviewed at this checkpoint: pulse acquisition, concurrent pacing, actual
phase separation, staged runtime and final custody. No native replay occurred.

## Main-agent response before formal freeze

Ten effective red subtests reproduce stale ID, wrong order, out-of-window
capture, partial/mislabeled/type-invalid plan, bool/float stream joins,
duplicate/nonfinite journal records. After fixes, all19pure test methods pass.
Audit imports no candidate code, independently reconstructs114ordered cases,
requires exact frozen fixture/source/auditor bytes in its CLI, rejects
cross-cue temporal overlap and uses strict typed JSON stream joins.
Original review and source checkpoints remain immutable history.
