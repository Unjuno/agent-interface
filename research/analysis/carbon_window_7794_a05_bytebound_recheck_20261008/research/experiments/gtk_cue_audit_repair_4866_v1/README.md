# Successor audit repair — Issue #4866

Allocation: `gtk-cue-audit-repair-4866-20260927-01`  
Parent evidence: #4862, preserved unchanged; initial STOP PR #4865.  
Branch: `research/gtk-cue-audit-repair-4866-20260927`  
Path: `research/experiments/gtk_cue_audit_repair_4866_v1/`

No fit, prediction, or recapture is authorized. This path will contain only the corrected raw-only audit, its frozen commands, integrity tests, and STOP/acceptance report.

Immutable source inputs from #4862:
- runner SHA-256: `f42ce1c014a5c6a50dd13efdbed083b63fce284386665254559b280e9ff87e75`
- formal result SHA-256: `d6eca8b564bbd391f3cae2f34c7948af16e07b27745370b2ad06abb1de7e9a6a`
- raw NPZ SHA-256: `11109f60ebfbab32a28d1c18239d736052786807bcf5be318a9c3f60d004a935` (retained locally; not committed on #4862 branch)

Corrected auditor must use a guaranteed value-changing float32 mutation and explicitly assert the mutation differs before the corrupted record is tested. No formal model execution.