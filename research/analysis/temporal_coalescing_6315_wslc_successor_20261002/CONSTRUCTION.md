# Construction record

Before formal allocation, native Ubuntu WSL (Python 3.12.3) ran:

```text
python3 -B -m unittest discover -s <candidate_src> -p test_construction.py -v
```

The first construction attempt ran 3 tests and failed 1: `_mutate` unpacked a mutation specification as a `(name, spec)` tuple even though the caller had already separated those fields. Error: `ValueError: too many values to unpack (expected 2)`. This was a test-harness construction defect, found before the formal candidate invocation count became nonzero. It was corrected to pass and consume the mutation spec consistently.

The same construction command was rerun once after the correction: 3/3 passed. It covered deterministic in-range candidate mappings, independent deadline/coverage truth classes, and rejection of the four frozen mutation controls. No formal candidate run occurred during construction.
