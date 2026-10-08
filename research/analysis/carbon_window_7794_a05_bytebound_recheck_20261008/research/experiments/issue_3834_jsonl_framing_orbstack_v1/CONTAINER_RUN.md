# Container run record — Issue #3834 formal-01

Host selected Docker context: `orbstack`; server: OrbStack 29.4.0, Linux/arm64. Image inspection resolved the exact pinned digest in `FREEZE.json`. Both invocations used network none, read-only container root, source mounted read-only, and bytecode disabled.

## Formal runner

The actual output directory was `/tmp/issue3834-formal01.pmc4qv`, created empty with `mktemp -d`. From the repository root, the equivalent command is:

```sh
OUT_DIR="$(mktemp -d /tmp/issue3834-formal01.XXXXXX)"
docker run --rm --network none --read-only --tmpfs /tmp:rw,size=64m \
  --mount "type=bind,src=$PWD,dst=/src,readonly" \
  --mount "type=bind,src=$OUT_DIR,dst=/out" \
  --workdir=/src --env OUT=/out --env PYTHONPATH=/src \
  --env PYTHONDONTWRITEBYTECODE=1 \
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  /bin/sh -c 'python -B research/experiments/issue_3834_jsonl_framing_orbstack_v1/validate_freeze.py && python -B research/experiments/issue_3834_jsonl_framing_orbstack_v1/runner.py'
```

Formal stdout:

```json
{"decision": "PASS_FRAMING_GUARD_SCOPED", "raw_sha256": "ff1a916ede722d07677977e942c72f8d7061e110e0cdbafb2e8cf09be68097ec", "rows": 5}
```

## Independent auditor

The independent auditor ran in a second fresh container. The raw file and source were both read-only mounts:

```sh
docker run --rm --network none --read-only --tmpfs /tmp:rw,size=64m \
  --mount "type=bind,src=$PWD,dst=/src,readonly" \
  --mount "type=bind,src=$PWD/research/experiments/issue_3834_jsonl_framing_orbstack_v1/results/formal-01,dst=/evidence,readonly" \
  --workdir=/src \
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  /bin/sh -c 'python -B research/experiments/issue_3834_jsonl_framing_orbstack_v1/validate_freeze.py && python -B research/experiments/issue_3834_jsonl_framing_orbstack_v1/audit.py < /evidence/raw.json'
```

Independent audit stdout:

```json
{"accepted_bytes":351,"accepted_sha256":"b027c295c619b525aa1ac1070c3a9b7a10fa754a7154c3ef44ecb89b51e5734a","decision":"PASS_FRAMING_GUARD_SCOPED","delivered_bytes":350,"delivered_sha256":"400e6dae93ce82dbf1815ac2ae9e2f9537bee92bbcf7e4affecdef950d3a4f02","errors":[],"report_sha256":"198c5a017a5d572c0202c11d4e852f224c2939c3840ba7670ae1fd199362009a","rows":5}
```
