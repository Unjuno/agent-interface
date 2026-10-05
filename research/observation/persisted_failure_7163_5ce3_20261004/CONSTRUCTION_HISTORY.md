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

Independent prelaunch Jason review: critical0, Important attached-client timeout
may leave own container live; explicit parent-owned ID+label checked stop/terminal
procedure added prospectively. Important archive provenance separate from audit;
explicit source/receipt/raw/ENV/mount/terminal/resource gate added before input.
Minor FRESH depended on memory file: new8th policy test with absent memory produced
FileNotFoundError (8tests/error1) before repair. FRESH now checks only current fields.
Only eight preparatory files existed, not parent's mistaken nine-file count;
seven source/test/README freeze inputs plus this HISTORY. A guessed workflow
path read failed before launch; actual workflow names discovered by git ls-tree.
