# Local construction CI (not formal container evidence)

Environment: macOS arm64, CPython 3.14.5; the same development replay was also run under CPython 3.12.13. These are host-side construction/replay checks, not formal container evidence. Latest recheck: 2026-10-01, all seven tests passed, `METHOD_PASS_SCOPED`, 13,824 states and 1,658,880 fair traces; independent auditor reported no errors. Candidate SHA-256 `5fcab832c45b2a081121aa68fd93eaf60d3e0826df0c71015d5e7b3d7de1746c`; audit SHA-256 `840bf1af12b5dffae95392dc2ea87cb1f46d5a7820c450b2f5d661f630442450`. See `raw/development/iteration-04-recheck/`.

Commands from this directory:

```sh
python3 -m py_compile model.py audit.py test_model.py
python3 -m unittest -v test_model.py
python3 model.py --output raw/development/iteration-03/candidate.jsonl
python3 audit.py raw/development/iteration-03/candidate.jsonl --out raw/development/iteration-03/audit.json
python3 ../check_index.py
git diff --check
```

Formal candidate and auditor must instead run once each in separate containers inside the assigned isolated OrbStack guest, using the exact image digest in `PREREGISTRATION.md`. Host execution is construction only. Never overwrite `raw/development/iteration-01/` or formal output.
