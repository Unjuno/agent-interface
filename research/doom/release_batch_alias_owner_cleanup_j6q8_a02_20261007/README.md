# A02 — guarded alias refusal followed by actual owner close

This is a separately frozen construction successor after the A01 runner setup STOP. A01 invoked the candidate with the already-existing bind-mount root as its output path, while the candidate requires a fresh directory. It stopped before Xvfb startup and emitted no candidate raw file. A01's exact stop record is preserved in `PREDECESSOR_A01_STOP.json` and in A01's own evidence folder.

A02 changes only the output invocation to a fresh nonexistent subdirectory (`/out/A02`). The candidate code, V4→V3→V12 source chain, candidate-only two-line resolved-keycode guard, and decision gates are unchanged. This does not retry A01's failed invocation and remains a construction test, not a live allocation.

See `FREEZE.json` for H/T/D/C/U, exact source hashes and Git blobs, image identity, resource limits, one-shot command, and preflight. `PLAN.md` carries the readable protocol. The first candidate raw and raw-only audit are retained as `results/A02_RAW.json` and `results/A02_AUDIT.json`.
