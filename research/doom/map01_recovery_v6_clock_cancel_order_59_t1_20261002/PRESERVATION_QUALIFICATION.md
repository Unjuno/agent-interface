# Historical audit-STOP chronology clarification (2026-10-02)

Preserve the original `STOP_AUDITOR_ROOT_PATH` and all frozen source, raw trace, error record and report bytes unchanged.

The retained auditor source reads and parses `raw_trace.json` before its first Git source-retrieval command. The recorded `fatal: not a git repository` occurs at that first retrieval because `HERE.parents[3]` selects the parent of the repository. Thus the historical wording “before loading the raw trace” is imprecise: the failure happened after raw loading but before source verification, timing-gate evaluation or an independent audit result.

This clarification does not repair or rerun the auditor. The separately retained #6236/#6239 audit remains a distinct successor and does not overwrite this allocation's STOP. No new runtime, MAP01, physical-input, safety or efficacy claim is made.
