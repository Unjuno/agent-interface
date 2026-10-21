# Sanitized public evidence

This directory contains the conditions, sanitized one-trial receipt, audit,
redaction record, and setup-stop trace for the public standard-caller Fake X
characterization. The unredacted raw result remains in the adjacent local
`raw/` directory and is not included here. Values and uncertainty classifications
are unchanged by redaction.

Run `python -B audit_raw.py` from this directory to check the published receipt.
`SHA256SUMS` records the byte hashes of the public packet files. The result is a
single Fake X characterization; it does not establish a physical release,
reliability rate, or product response bound.
