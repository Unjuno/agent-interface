# Pre-input construction history

Policy TDD: `python3 -B -m unittest test_policy` against no-store/UNKNOWN stub
ran7, failed4 (reload recurring block, cleared TRY, new-hazard selective TRY,
exclusive first-record write). Other3 coincidentally passed the conservative stub.
Minimal persisted implementation then ran7 PASS.

First combined checker construction `python3 -B -m unittest test_policy test_audit`
ran13, error1: `test_copied_controls_effective_and_rejected` raised
`ValueError: ineffective corruption`. First control set row0 NO_MEMORY decision
to TRY, its existing value. Before any source freeze/native input, changed this
control to row2 TYPED recurring BLOCK→TRY. Original construction error is retained
here; it is not a native result or consumed formal allocation.
