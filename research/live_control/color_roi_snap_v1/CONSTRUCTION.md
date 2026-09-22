# Construction history — excluded
1. construction-01 STOP_OUTER_TOOL_TIMEOUT after 8 complete cases: fixture SIGTERM did not exit promptly. Repair: explicit owned stop-file; require fixture exit0.
2. construction-02 STOP_CANDIDATE_RAW_TYPE at 10/12: python-xlib returned str for all-background ROI. Repair: latin-1 normalization; bytes path unchanged.
3. construction-03 PASS 12/12, audit errors0, 10/10 corruption controls rejected.
4. construction-04 source consolidation only: same candidate/case semantics moved into study.py to simplify publication. Re-run required before freeze. Formal invocation count 0 throughout.
construction-04 result: PASS_CONSTRUCTION_SCOPED, same 12-cell one-repetition matrix, audit errors=[], 10/10 controls rejected, fixture exits0 and Xvfb cleanup verified. This is the source version frozen for formal use.
