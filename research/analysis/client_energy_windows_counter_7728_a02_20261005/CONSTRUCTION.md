# A02 construction

Construction checks do not access the EMI device or sample live counters. From this directory:

    python -B -m unittest -v test_audit_a02.py

The frozen candidate `run_a02.ps1` is invoked once, then `audit_a02.py` once. Do not repeat either live operation to repair output or an audit.
