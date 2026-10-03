# T8 construction record

The validator reads only the immutable captured stdout copy, enforces its exact byte count/SHA-256 before parsing, checks a strict nine-key JSON schema and exact typed values, and emits its result with exclusive file creation. It imports no T6/T7 candidate or auditor code and uses only Python's standard library.

The construction/mutation suite was run before freezing:

```text
python -B -m unittest -v test_validate_receipt.py
```

Observed: 7 tests passed, 0 failed. The cases cover the exact retained receipt, altered byte identity, changed key set/field name, wrong count, wrong status, non-empty errors, and booleans masquerading as integer counts. These checks did not execute the one-shot formal CLI. Before the freeze commit, `formal_validation.json` did not exist and formal CLI invocations remained zero.

The captured input copy was read back as 306 bytes with SHA-256 `604fc18e94e80f6aa941623b8854ffad88043e16e5058db89aa45449ba97489f`, matching the immutable blob in PR #6983.
