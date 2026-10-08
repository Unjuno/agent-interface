# Construction log

- Initial command from repository root, `python3 -m unittest -v research.analysis.effect_interference_5366_t2_v1.test_construction`, failed before any formal invocation because the test imports the local `candidate` module and the package directory was not on `sys.path`. Exit 1. This is a harness invocation error; candidate=0, auditor=0, retries=0 at that point.
- Corrected construction command from this directory, `python3 -m unittest -v test_construction`, passed 5/5.
- `python3 -m py_compile candidate.py audit.py` passed under CPython 3.14.5, macOS arm64.
- Five exact source SHA-256 values were inserted into `FREEZE.json` before the formal candidate and auditor invocations. The formal freeze is pinned to main commit `c69fa71501a0e42abc3ffe435ae72949d5d15877`.
- The post-run checksum-verification command was twice launched from the repository root even though manifest entries are package-relative; both attempts therefore reported path/read failures and apparent hash mismatches. No source or raw file was changed. Verification from the package directory passed for every listed file; do not invoke this manifest from the repository root without adding its package prefix.
