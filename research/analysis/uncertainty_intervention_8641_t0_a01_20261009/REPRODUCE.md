# Read-only reproduction

Use the retained raw candidate file to reproduce the independent audit only:

```sh
python3 src/auditor.py input/protocol.json input/fixture.json input/oracle_fixture.json raw/candidate.json /tmp/8641-audit.json
cmp audit/audit.json /tmp/8641-audit.json
```

The formal candidate command in `FREEZE.json` is recorded for provenance but must not be invoked again. Construction-only mutation checks are listed in `FREEZE.json` and use disjoint construction rows.
