# CACTUS_NEEDLE3 base structured-action delegate — first rung

Status: construction complete; no formal model calls yet. One explicitly excluded smoke prompt exposed a malformed field-value failure (`Display_name` instead of `Mica`) with a successful `SET_FIELD` wrapper. This is diagnostic only, not a formal row or acceptance result; retained output is local at `artifacts-local/cactus_needle3_20260926/construction-run-03.log` and will be summarized in `CONSTRUCTION.md`.

Allocation `cactus-needle3-base-structured-action-20260926-01` is a fresh continuation of Issue #4204. It preserves the prior `STOP_MODEL_OR_PROVENANCE_UNAVAILABLE`. It tests one deterministic, authority-neutral settings simulator and the official unadapted Needle 3 base. The model is not allowed to emit OS/GUI input; every proposal is recorded before the simulator's independent admission gate.

H/T/D/C/U, the seven fixed cases and the acceptance rules are in `CASES.json` and the public Issue #4204 claim. No fine-tuning or depth sweep. The published full base artifact and Linux x86_64 engine wheel are hash-pinned from Hub revision `b274efcb211a9eef48c9a88da4b43bd569696a39`. The Python client is a distinct PyPI wheel, `cactus-needle==3.0.1`, and its exact wheel plus dependencies are retained locally and hashed separately in `CLIENT_WHEELS.sha256` (the local x86_64 CPython 3.12 wheelhouse totals about 7.4 MB). The Hub engine wheel is not the Python client: it contains the native `libneedle3.so` binary only. Keep the two wheelhouses separate so pip cannot select the engine-only wheel in place of the client. The native runtime is CPU-oriented and tiny; this allocation uses the local PC's Docker runtime but does not pass through the RTX 3080 or claim GPU inference.

## Construction

Construction may verify import/loading and use separately labeled prompts that are not in `CASES.json`. Construction data is never pooled with formal rows. Do not invoke the frozen formal runner until all source and artifact hashes are committed and read back from GitHub and the preformal ownership check is current.

The Python client was installed from its PyPI wheel and the native engine from the separately named Hub wheel. Two earlier container setup attempts stopped before import/inference because the engine wheel was misidentified as the client; a third stopped because its mount filename was not a valid wheel filename. These are preserved as packaging failures, not model outcomes. The fourth setup used correct identities and completed the excluded smoke call.

## Formal path

Run once using the frozen host launch command after artifact/image/path checks. The formal container uses the locally cached pinned Python image, no network, read-only root/source/model/client-wheelhouse/engine-wheel, bounded CPU/memory/PIDs, no capabilities, telemetry off, and a fresh output mount. The only writable container paths are `/tmp` and `/output`. `runner.py` refuses a pre-existing result file and validates source/model/wheel identities before loading Needle. The separate auditor consumes raw output only; no reruns or replacements.

## Scope

One synthetic settings skill, seven cases, one model revision and depth, one local PC. Even a PASS is not general GUI competence, production authority, cross-device equivalence, or integrated Agent Interface efficiency. The macro is an intentionally strong fixed-corpus baseline.
