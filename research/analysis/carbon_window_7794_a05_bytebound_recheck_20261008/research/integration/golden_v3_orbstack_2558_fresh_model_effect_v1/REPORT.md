# #2558 fresh OrbStack model-to-effect allocation

Date: 2026-09-20 (Asia/Tokyo)

## H/T/D/C/U

- H: a fresh private X11 fixture running inside OrbStack can receive a host-local Codex compiled grounding plan, pass independent schema/bounds checks, execute a guarded program, and produce an independently scored effect.
- T: start `runtime/native_result_self_use.py` in a fresh Docker container under `orbstack`; capture a new observation; call host-local `codex exec` on that image; validate the returned compiled-form-grounding-v1 plan in a second OrbStack container; use its field point to submit the preregistered fixture token; independently read the effect and verify release.
- D: fresh image `before.png` SHA256 `039709a70f6e2269c33e8eb7425954114aaa4f871dc06b9dc27fc33e248c84db`; fresh after image SHA256 `92aabf3c35f987a565382347f9bf0a895796266d4a04ecf5ee46b0330e92cbb5`; model returned field (130,55), submit (51,101); OrbStack schema/bounds validation PASS; token `docker2558-fresh`; independent effect `saved=true`; action-to-scored-effect 112.449ms; release verified; cleanup completed. Model usage: 15,947 input / 179 output / 64 reasoning.
- C: `PASS_FRESH_MODEL_TO_EFFECT_SCOPED`. This proves a fresh container allocation from observation through model-produced field point to an independent fixture effect. It does not claim the full six-task golden route or general reliability: `visual_target_revalidation=false`, and the model submit point was not used by the native self-use harness.
- U: add the independent visual target/focus/geometry revalidation path and consume the model's complete plan (including submit/revalidation method) before action; then repeat the preregistered cold/warm/invalidation/repair workload.

## OrbStack provenance

- Docker context: `orbstack`
- Docker Server: 29.4.0
- Linux kernel: `Linux-7.0.14-orbstack-00380-ga7e0a2dc9535-aarch64`
- OrbStack: 2.2.3
- Fresh run used a private Xvfb display, new fixture process, and new observation artifact.

## Evidence hashes

- result.json: `fdfaf8f68b773d9cf276ce8553c3a55abf09efbee0238ee3f2b10d7b440e86df`
- evaluation.json: `fd7af63998f264d0dc05797fcf049be8102102f550a7016ceef29f791cd4da73`
- effect.json: `c32360810bb87fe348f9516d8398b9c1b1cfac0fa6c178701ea758248f9e8c12`
- cleanup.json: `5dda992043281bd9592f25492912aef01b8f3f8b1716f90b41e8da912b4a1993`
- model-events.jsonl: `ef1b2e1318fd74b20f51ac9084f40478743e7fac5da04a3d17de4b03cd525537`

This is additive evidence for #2558. Earlier STOP and boundary-replay results remain immutable.