# #4387 result — unequal source intervals

**PASS_UNEQUAL_INTERVAL_APPLICABILITY_SCOPED** for fresh allocation `reversal-geometry-g8m2-02`.

The originally proposed 360-row matrix was accidentally executed during construction before public freeze and remains `STOP_WORKFLOW_INTEGRITY_PREEXPOSURE`; it is not pooled. The authoritative allocation uses fresh interval pairs `(80,15),(15,80),(120,20),(20,120),(60,140),(140,60)` ms and fresh reversal ages `{2,17,55,105,190}` ms plus constant controls.

Formal first outcome: 360/360 rows, process exit0. Unchanged legacy float heuristic has 26 wrong singleton directions; exact-rational transcription disagrees 0 times. Continuous feasible-set candidate has 0 wrong singleton directions, contains the true direction in 360/360 rows, and returns an informative singleton in 126/360. At least one observed payload admits both current directions, so UNKNOWN is required there. Independent separately structured exact-rational auditor: 1,086 checks, errors=[].

Directed example: geometry 80/15 ms, post direction LEFT, reversal age2 ms, observation errors(-0.75,0,+0.75)px. Legacy returns RIGHT while the exact feasible set is {LEFT,RIGHT}; candidate returns UNKNOWN. This is a contract-level counterexample, not an empirical failure rate.

Corruption validation: initial copied-record control set rejected9/10; the non-rejection was an intentionally changed oracle/post label on a row already feasible in both directions, so the mutation was non-effective for the audited gate and is retained. V2 uses nine effective row/gate mutations; 9/9 reject normally. Frozen study/auditor/source hashes are unchanged after formal.

Scope: known speed73px/s, exact source timestamps, per-point error <=1px, constant motion or at most one reversal, query at newest source sample. No later action-time validity, GUI/input, model/provider, performance, natural failure probability, runtime promotion or product claim. Global ROADMAP and parent Issues remain open.
