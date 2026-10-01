# Local construction CI (not formal container evidence)

Environment: macOS arm64, CPython 3.14.5. Commands from this directory:

```sh
python3 -m py_compile model.py audit.py test_model.py
python3 -m unittest -v test_model.py
python3 model.py --output raw/development/iteration-03/candidate.jsonl
python3 audit.py raw/development/iteration-03/candidate.jsonl --out raw/development/iteration-03/audit.json
python3 ../check_index.py
git diff --check
```

Formal candidate and auditor must instead run once each in separate containers inside the assigned isolated OrbStack guest, using the exact image digest in `PREREGISTRATION.md`. Host execution is construction only. Never overwrite `raw/development/iteration-01/` or formal output.
