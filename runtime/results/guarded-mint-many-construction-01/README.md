# Guarded reference batch construction checks

Integration candidate on base 2207354ba293d87b4723c6e62a4d12a0fc2ec16f. Reuses the existing shared bridge mint operation for 1..8 explicitly grounded references from one delivered source. This combines registration requests only; it adds no action queue, autonomous target discovery, input replay, semantic assertion, or model.

Motivation: primary guarded-brief trial03 used three initial single-reference registrations and two more after layout change, plus one unexpected recovery registration. The field/submit pair also already exists in research/live_control/integrated_efficiency_client_v1.py. No published timing or economics claim for batching is assumed.

Construction verification: 251 protocol and 106 harness tests passed, including actual stdio SDK transport for the nested reference schema. New tests cover ordered same-source registration and read-only retention; a second-item persistence exception preserving the first success while leaving later items unattempted; duplicate aliases before connection opening; and full-batch syntax validation before any mint. Exact full logs are archived with hashes. These are construction checks, not successful primary GUI use or reduced model-token/latency evidence.

Planned primary validation: one fresh six-task A,A,A,B,B,B fixture, seed 991334. Use a three-reference initial batch grounded from the actual first image; separate entered-value review and Save; deliberate old-field refusal at layout change followed by a two-reference batch; finish all six, retrieve retained batch results without reminting, then explicitly close. Retain all failures and independent exact-once history. Never read oracle state before interaction ends. Host text/image callbacks pass content unchanged. This is usability validation, not a matched speed or token experiment. No new fixture is currently running.

Integration remains provisional until primary validation and final CI pass. The previously merged single-reference tool remains available unchanged.
