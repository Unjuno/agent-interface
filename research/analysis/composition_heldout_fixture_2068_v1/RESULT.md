# Result — composition held-out fixture v1

Decision: **PASS_COMPOSITION_HELDOUT_FIXTURE_SCOPED**

## Frozen execution evidence

- workflow: Composition held-out fixture v1
- run: 35443464575
- job: 105898269600
- runner: Ubuntu 24.04
- Python: 3.13
- artifact: 10584980393
- artifact SHA-256: `fcdbc9f20da64cf1a3731ab7d525272e9d4769ed4214cb3a24858a7ccfd46754`
- artifact size: 742 bytes
- py_compile: PASS
- fixture process: PASS
- reruns/tuning: 0

## Scope

The frozen deterministic fixture enumerates 10 controls across baseline, composed, and fallbacks-disabled arms. It retains separate task/effect outcomes, UNKNOWN/STOP, cue-use, raw fallback, retry, preflight and skipped-stage accounting. The independent oracle asserted zero unsafe rows and retained raw evidence.

This is a source/fixture and CI execution result only. It does not establish model behavior, GUI correctness, task utility, token or latency benefit, or transfer to DOOM/production. The later model-facing rung remains unverified.