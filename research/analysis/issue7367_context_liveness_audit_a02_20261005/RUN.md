# A02 audit-only run recipe

Run construction validation before freeze:

```sh
python3 -m unittest -v research.analysis.issue7367_context_liveness_audit_a02_20261005.test_workload_binding
python3 -m py_compile audit_a02.py test_workload_binding.py construction_tests.py
```

After freezing and committing the manifest/source, run the v2 auditor exactly
once in the already inspected `linux/arm64` OrbStack image. The candidate count
is zero by design. Mount the package read-only and a separate empty output
directory read-write. If the invocation fails, preserve its first output and
record STOP; do not retry or replay the candidate.

```sh
docker run --rm --pull=never --network=none --platform linux/arm64 \
  -v "$PWD":/src:ro -v "$PWD/formal_01":/out:rw -w /src \
  docker.io/library/python@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3 \
  python3 audit_a02.py --freeze FREEZE.json --out /out/AUDIT_V2.json
```

The v2 auditor imports the frozen A01 auditor to reconstruct the retained
semantic checks only after its own byte-binding gate succeeds. Its mutation
control reads only frozen copies and never invokes the A01 candidate.
