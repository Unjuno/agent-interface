# Actual assistant Calc use with persistent receipts

`journal-calc-01` uses unchanged interactive_v17, Linux/X11 and LibreOffice Calc.
Task: A1=532, A2=590, save sheet.xlsx in Excel format. The assistant viewed 001.png
(empty A1 selected), submitted cell input and save, inspected terminal receipt
sequence 11 → 007.png (format confirmation), confirmed the selected Excel format,
then inspected sequence 19 → 015.png before independent evaluation.

The first submit used `chord` with a keys array, which the interface rejected
before accepting or executing any part of the program. Source inspection revealed
the actual modifier/key fields. A corrected program entered both values and saved.
Its completed terminal did not mean the document was saved: the format modal still
required a new program. The assistant used the receipt image to make that decision,
then submitted Return/settle under a fresh authority envelope referencing delivery:21.

Independent evaluation succeeds; separately loading saved sheet.xlsx confirms
the two required cell values. The audit verifies 19 exact reconstructed frames,
33 matching output/flush IDs, source hashes, all declared evidence references,
two completed/released programs and no acceptance of the rejected first program.
Full workbook collateral, human speed comparison and actual tokens are not audited.
This familiar task family is development evidence, not held-out qualification.

The initial error exposed incomplete basic-operation discovery. New experimental
interactive_v18 advertises text, key and chord examples in ready. The audit extracts
those literal examples from the actual source and validates them against session_v16;
it also checks rejection of the original wrong chord form. V18 has no live execution
evidence yet, and examples are not a complete machine-readable operation schema.
Prior runtime files and failure evidence remain unchanged.

This extends persistent-receipt self-use from terminal typing to a desktop grid
and modal format transition. It does not establish task speedup from the journal
change. Next address discovery across all supported operation fields and use a
matched comparison to distinguish schema-related retries from planner delay.
