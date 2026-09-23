# #1819 retention note

The first reservation branch `research/temporal-query-cost-breakeven-1819` is not the merge candidate.

The deterministic formal had already run once from the source frozen in `SOURCE_FREEZE.sha256`. During GitHub retention, shortened but semantically equivalent `formal.py` / `audit.py` text was initially uploaded, then replaced with the exact executed source before any PR existed. No formal rerun, replacement, or tuning occurred.

To keep merged history source-exact and free of those intermediate retention-only commits, this r2 branch was created from a later current `main` and carries only the final exact source, result, audit, report, and source-freeze files.

The original branch is preserved as provenance and is not merged.
