# Conditions — Windows current-main preview builder R01

- Source commit: `39cbd0d202db82baf4886f1d781461909c4f706a`.
- Python: 3.11.9; Windows PowerShell; Git `core.autocrlf=true`.
- Checkout: sparse; the release bundle selection requires tracked paths outside the sparse set.
- Commands/results are retained in `raw/`; existing `test_build_preview.py` tests passed 6/6.
- No package dependencies were installed and no supported-host/live acceptance command was run.
- First build failed on retained source bytes; after exact blob restoration and 29/29 hash reconciliation, a second build exited 2 for 22 missing tracked paths. Preserve both outcomes.
