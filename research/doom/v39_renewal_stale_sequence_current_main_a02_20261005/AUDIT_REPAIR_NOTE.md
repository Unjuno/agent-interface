# Audit harness repair

The first independent-auditor launch mapped the source repository path basename directly to the snapshot file and stopped with `FileNotFoundError` before reading any test outcome. The candidate and its normal/optimized raw results were unchanged. The auditor now maps each frozen repository path to its actual `baseline_*.py` snapshot filename and audits the already-retained outputs; no candidate test was rerun.
