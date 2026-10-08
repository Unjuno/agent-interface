# Construction record

Before formal allocation, native Ubuntu WSL (Python 3.12.3) ran:

```text
python3 -B -m unittest discover -s <candidate_src> -p test_construction.py -v
```

The first construction attempt ran 3 tests and failed 1: `_mutate` unpacked a mutation specification as a `(name, spec)` tuple even though the caller had already separated those fields. Error: `ValueError: too many values to unpack (expected 2)`. This was a test-harness construction defect, found before the formal candidate invocation count became nonzero. It was corrected to pass and consume the mutation spec consistently.

The same construction command was rerun once after the correction: 3/3 passed. It covered deterministic in-range candidate mappings, independent deadline/coverage truth classes, and rejection of the four frozen mutation controls. No formal candidate run occurred during construction.

## Published-package path correction (post-formal, 2026-10-02)

After publication, a package-level construction invocation failed during test-module import because `test_construction.py` pointed to the private staging path `inputs/auditor_src/auditor.py`, while the published independent auditor is at `inputs/auditor/auditor.py`. No test method, candidate, or formal auditor invocation ran in that failed attempt. The test path was corrected to the published layout without changing candidate, auditor, fixture, or any frozen formal raw output. The frozen construction-test digest `0960e4e8890355175e803ce448af384c94135a375b9c2ac0d8999f4fdfa06013` remains in `FREEZE.json` as the preformal source identity; corrected published Git-blob digest is `519abf4a7ee40b907e8bc4bd2e7b3f01cc31780e7e17c04d2fb9deca69ebc3bb`.

The published test suite was then run from the package itself with Windows CPython 3.12.10 using `python -B -m unittest discover -s inputs/candidate -p test_construction.py -v`: 3/3 passed. This is a post-publication packaging/construction check only, not a WSLc runtime comparison or a rerun of the formal candidate/auditor allocation. The formal raw files remain byte-for-byte unchanged.
