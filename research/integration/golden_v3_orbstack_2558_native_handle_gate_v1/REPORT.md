# #2558 fresh OrbStack native-handle gate experiment

Date: 2026-09-20 (Asia/Tokyo)

## H/T/D/C/U

- H: the model-produced field point can be converted into a scoped native handle, revalidated against current focus/surface/geometry/pixels, and admitted for action; a controlled focus change must fail closed with zero input emissions.
- T: start a new private Xvfb fixture in OrbStack with native artifacts and `native_handle_bridge_v1`; obtain a fresh observation; call host-local Codex; submit its field point after native handle admission; independently score the effect; run the preregistered focus-change reuse probe and read-only continuation.
- D: fresh run produced `saved=true` for `docker2558-handle`; visual target revalidation=true; action-to-scored-effect 154.205ms; release verified; continuation used no input replay. The focus-change probe changed focus from 2097173 to 1293 and returned `SCOPE_MISMATCH`, `input_dispatched=false`, `emissions_delta=0`. Model usage: 16,142 input / 195 output / 80 reasoning. Fresh before image SHA256 `839b1c4a62eca7b4b774b7f1d7bf50635a7b8bc5a31b5567b30e715b16d5afc8`; after image `4ad1237834f35166d613b1d78f79ce5882cf2e0ab6771276dd1e65395238d40a`.
- C: `PASS_FRESH_NATIVE_HANDLE_EFFECT_AND_FAIL_CLOSED_GUARD`. This is stronger than the previous scoped run: fresh model-to-effect, native revalidation, verified release, read-only continuation, and invalidation refusal all passed. It is still not the six-task golden route or a general reliability claim.
- U: integrate the model submit/revalidation method into the native handle path and run the preregistered cold/warm/invalidation/repair workload across the full route.

## OrbStack provenance

- Docker context: `orbstack`
- Docker Server: 29.4.0
- Architecture: linux/aarch64
- OrbStack: 2.2.3
- New private Xvfb and fixture process per allocation.

## Evidence hashes

- result.json: `99314e1ddb9cc6d38af77503f24b9da1d95648bcb254cb73210d17afd076a845`
- evaluation.json: `5e2bed9da648d8844296c5d301286f97ff5db54fa2ed7e88d9a18cc9680422270`
- guard-focus-change.json: `cb3eaa9f3cb0c590102964a1ae9418ef2371c947502f574d2c7c22511a3677e5`
- continuation.json: `73c9c14e954e64c465af36b90f8033e6ec3de674f747adc3556085113bb708fe`
- effect.json: `ef20b11d2fb63af3f27faaa580f20981e00d6819a5a6dfd18ebdfbd2f6d93e9b`
- model-events10.jsonl: `d7fc7d08372687719713079e95abe6ba77f2c89e73f0a8ac393daf3541a48bef`

Previous STOP, replay, and scoped fresh results remain immutable.