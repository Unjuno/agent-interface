# Boundary-blame replay on retained receipts

Successor rung for [Issue #5313](https://github.com/Unjuno/agent-interface/issues/5313), following its synthetic T0. This package reads the already-retained #59 app-server diagnostic records on main; it does not rerun their native processes or modify their results.

See `PROTOCOL.md` for H/T/D/C/U. Construction checks:

```sh
python3 -B -m unittest discover -s . -p 'test_*.py' -v
```

After exact source and input hashes are posted as a pre-run freeze receipt, invoke `python3 -B run_candidate.py` once and `python3 -B audit.py` once. Do not rerun either formal command after outputs exist. The original #59 evidence package is referenced by repository-relative path and its existing `SHA256SUMS`; formal output snapshots every input digest consumed by each case. The independent auditor reopens raw bytes and independently verifies that frozen manifest, its digests, lifecycle, journal joins, source, and output bindings.
