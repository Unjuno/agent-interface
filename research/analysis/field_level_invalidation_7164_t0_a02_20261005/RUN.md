# Frozen run recipe

Construction checks run on the host before freeze and are not formal results:

```sh
python3 construction_tests.py
python3 -m py_compile candidate.py audit.py construction_tests.py
```

Formal execution is limited to one candidate invocation followed by one auditor
invocation, sequentially, with the frozen image digest and no network. The image
must already exist locally; do not pull it. The output directory must be empty.
If either invocation fails, preserve its output and record STOP; do not retry.

```sh
docker run --rm --pull=never --network=none --platform linux/arm64 \
  -v "$PWD":/src:ro -v "$PWD/formal_02":/out:rw -w /src \
  docker.io/library/python@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3 \
  python3 candidate.py --input INPUT.json --schema SCHEMA.json --freeze FREEZE.json --output /out/candidate.json

docker run --rm --pull=never --network=none --platform linux/arm64 \
  -v "$PWD":/src:ro -v "$PWD/formal_02":/out:rw -w /src \
  docker.io/library/python@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3 \
  python3 audit.py --input INPUT.json --schema SCHEMA.json --freeze FREEZE.json \
  --candidate-output /out/candidate.json --output /out/audit.json
```

The host candidate and auditor are not run after freeze. Only the frozen
container invocations produce the candidate/audit formal output pair in
`formal_02/`.
