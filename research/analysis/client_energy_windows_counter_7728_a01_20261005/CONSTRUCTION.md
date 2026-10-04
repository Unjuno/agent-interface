# Construction checks

These checks exercise only source parsing and the independent auditor's synthetic controls. They do not call the EMI device interface or read a live sensor.

Run from this directory:

    python -B -m unittest -v test_audit_preflight.py

The frozen live probe is run_preflight.ps1; it must be invoked once, followed by one invocation of audit_preflight.py. Do not rerun the sensor probe to repair an audit or output problem.
