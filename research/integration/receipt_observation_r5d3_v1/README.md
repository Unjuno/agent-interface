# Complete receipt observation — #4361

Additive research, not runtime promotion. Preserve #4231; its receipt_ns is an owner pre-output timestamp, not caller arrival. Correction: Issue #4231 comment5832396571.

The SOURCE capsule is the exact preformal source/plan/proof/environment freeze (14 files). Concatenate the six binary SOURCE parts, verify SOURCE_PACK.json, or use the bounded data-only reader:

```sh
python -S -B restore.py SOURCE /tmp/r5d3-source
```

Read PLAN.md and PROOF.md in the restored directory. They define the 24-session, two-reader/four-schedule/three-repetition test and all H/T/D/C/U limits. Producer stamp, complete validated reader observation and effect-fsync brackets are different endpoints. No result or authority follows from the source freeze alone.

Formal commands after public byte-identity readback, each once:
```sh
python -S -B execute.py formal 0
python -S -B execute.py formal 1
python -S -B execute.py formal 2
```
Do not rerun consumed formal batches. Final evidence/read-only reproduction will be added after the first outcome. Restorer paths are a trusted quiescent publication directory, not a hostile-filesystem security sandbox.
