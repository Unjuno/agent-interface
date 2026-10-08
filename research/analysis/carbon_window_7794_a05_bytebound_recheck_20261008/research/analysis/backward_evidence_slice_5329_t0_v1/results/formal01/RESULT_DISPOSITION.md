# T0 result disposition: STOP_PROVENANCE_OR_RUNNER

The frozen Docker runner completed once and emitted four rows. Raw SHA-256:
`9bd3d3db35434e4a4ef689d942a77d42d089f055de9c856da641d74cd173248b`.

The single frozen independent-auditor invocation exited 1 before producing an
audit result. Its independent closure traversal raised `KeyError:
'external_cause'` on the deliberately unresolved external-cause edge. The
frozen graph uses that dangling node to mean the dependency is unknown; the
auditor assumed every edge target was present in the node table. This is an
auditor construction/provenance failure, not a scientific FAIL or PASS.

Final disposition is **STOP_PROVENANCE_OR_RUNNER**. Do not patch this allocation,
rerun its runner/auditor, or infer a method result from the raw alone. A corrected
implementation would require a separately frozen successor allocation and a
new output path. No task, model, GUI, GPU, or external effect was involved.

Frozen source hashes:
- runner.py SHA-256 `CA73B33EF3B7483F3A5CC9ECD0354B91401873FF6F9C7FED87B42BA11581AA7F`
- audit.py SHA-256 `2BA795477E23085FF2BB0D46D2FA6A50DF98D6CF486B609A06F8C0DA0CE49A50`
- image `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
- issue freeze #5329 comment #5924039650

## Immutable audit attempt

```text
Traceback (most recent call last):
  File "/src/audit.py", line 54, in <module>
    expected_retained = sorted(nodes) if key == "full" else independent_closure(nodes, allowed)
  File "/src/audit.py", line 18, in independent_closure
    for link in nodes[current].get("edges", []):
KeyError: 'external_cause'
```

