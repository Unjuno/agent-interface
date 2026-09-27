# Excluded construction record

This is setup evidence only. It is not part of the frozen seven-case formal sample and must not be counted as a result.

## Successful excluded smoke call

- Local Windows PC, Docker Linux container, `python:3.12-slim` image pinned by digest `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
- Network disabled; 2 GiB memory, 2 CPUs, 64 PIDs, all capabilities dropped, read-only root with bounded `/tmp`; Hub model and two separate wheel sources mounted read-only.
- Hub model revision `b274efcb211a9eef48c9a88da4b43bd569696a39`; model artifact SHA-256 `c9d915eca282ed42d1a09b143b592adb4cc6744ffe2d294adf5cfc5548170c38` (35,335,380 bytes).
- PyPI client `cactus-needle==3.0.1` SHA-256 `d990c623ecc69f7c7692d31678e88a799caced87780d7fed31c55b6961d75c82`; separate Hub engine wheel SHA-256 `05770ef9a85686583968ea15f62f9ad44217e078efda99559d3208bb8a369b0`.
- Prompt, intentionally absent from `CASES.json`: “For workspace demo at generation 3, set display_name to Mica”.
- Observed wrapper-level `success=true`, but emitted `SET_FIELD(field="display_name", value="Display_name", generation=3, scope_id="workspace")`. This is semantically wrong and demonstrates why wrapper success is not task success. No admission gate or formal scoring was applied to this construction prompt.
- Decision latency 2805.900459 ms; peak RAM 106.5 MB; decode 50.8 tokens/s; prefill 191.4 tokens/s. Single smoke observation only; not a latency estimate.
- Exact raw stdout/stderr is retained locally, excluded from git, at `artifacts-local/cactus_needle3_20260926/construction-run-03.log`.

## Failed setup attempts (all before model invocation)

1. Attempt 1 passed the Hub engine-only wheel where the PyPI client wheel was expected; pip rejected the non-wheel filename.
2. Attempt 2 mounted the engine-only wheel at a mismatched path and pip could not find it; package inspection then established the Hub wheel contains the native engine, not the Python client.
3. Attempt 3 mounted that engine wheel as `/engine.whl`; pip rejected the renamed, invalid wheel filename.
4. Attempt 4 mounted the wheel at its exact valid distribution filename and separately installed the PyPI client; setup and the excluded smoke inference completed.

The first three outputs remain in the local ignored `artifacts-local` directory. None called the model and none are formal STOPs for the allocated model evaluation.
