# MAP01 r4 side-effect-free import-boundary successor

Successor Issue: #2038. This additive path addresses the audit finding in
#2007: supplying `--out` does not make the launcher gate side-effect-free
because the entrypoint invokes the scientific `main()`.

The gate in `import_gate.py` is source-only. It compiles the retained
successor entrypoint and rejects forbidden launcher/science calls. It reports
zero construction/formal/input/model/network counters. It does not establish
import readiness, construction compatibility, physical occupancy, gameplay,
latency, or any MAP01 formal result until a separately reviewed workflow
executes it with the exact source and environment manifest.

No parent artifact is modified or rerun.
