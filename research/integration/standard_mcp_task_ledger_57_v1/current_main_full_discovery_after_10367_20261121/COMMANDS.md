# Reproduction

Run from the repository root on Windows CPython 3.11.9 at main
`6f33f6ac2d263d2183b8f730c087115afbf0414c`:

```powershell
python -m unittest discover -v -s research/integration/standard_mcp_task_ledger_57_v1 -p 'test_*.py'
python -O -m unittest discover -v -s research/integration/standard_mcp_task_ledger_57_v1 -p 'test_*.py'
```

The same two commands were run once more for R02 and saved separately. The
isolated Windows cancellation selector was run from the integration test
directory after setting `PYTHONPATH` to the absolute repository and integration
directory paths:

```powershell
python -m unittest test_partial_input_cancel_accounting.PartialInputCancelAccountingTests.test_cancel_after_first_transition_is_joined_without_replay -v
python -O -m unittest test_partial_input_cancel_accounting.PartialInputCancelAccountingTests.test_cancel_after_first_transition_is_joined_without_replay -v
```

Raw stdout/stderr is retained byte-for-byte under `raw/`; the packet-local
`.gitattributes` disables line-ending conversion for those files. Test-source
SHA-256 values normalize source text to UTF-8/LF. No Docker or live application
was used for this Windows full-discovery recheck.
