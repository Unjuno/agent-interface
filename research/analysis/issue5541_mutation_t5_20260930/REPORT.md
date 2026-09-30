# Issue 5541 T5: finite interaction-mutation probe

## H/T/D/C/U

- H: Single-mutant kill coverage can overstate interaction coverage; an independent contract oracle should detect any surviving safety mutant.
- T: Four typed cases and three Boolean fault operators; enumerate all seven non-empty operator combinations. This tests only a finite matrix, not production defect probability.
- D: The probe gate required all singles killed and at least one combination survivor. Independent replay recomputes kills from retained matrix. Result: FAIL; all singles were killed, but no combination survived.
- C: The four-case set may be too strong or the operator catalogue too weak to expose masking. Earlier T3 observed one hand-constructed masking interaction; earlier T4's different operator grid had zero survivors. Those historical outcomes are separate and unchanged.
- U: No useful mutation score, realistic fault likelihood, broad oracle-independence, runtime safety, GUI, or product claim.

## Execution record

- GitHub main at start: 55c467786b3b98e5f8d1746f9c2970b7ada8b47c.
- Existing image, no pull: python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f, linux/arm64.
- OrbStack server 29.4.0, aarch64; no running container observed before invocation.
- Docker flags: --rm --pull=never --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=1m.
- Container exit code 1, expected from unmet combination_survivor_exists assertion.
- Captured semantic hash: 4e853f1f020954e740b7b3918f50bbd98888b3009395d57f89395b9cf56323be.
- Stdout byte hash was not captured. A previously posted value was retracted; do not treat it as evidence.
- Retained result file docker-stdout.json SHA-256: 1ec1833171df24332fcd7e03b30e1b118a53120d3b2f8c5443cd5645bcf2253c.

## Local replay checks

The Docker invocation was not repeated. The retained result was replayed locally:

    python3 -m unittest -v
    Ran 3 tests ... OK
    python3 replay.py
    {"all_single_mutants_killed": true, "combination_count": 4, "decision": "FAIL_PROBE_GATE_NO_COMBINATION_SURVIVOR", "raw_semantic_hash_recomputed": "4e853f1f020954e740b7b3918f50bbd98888b3009395d57f89395b9cf56323be", "raw_status": "FAIL", "survivor_count": 0, "survivors": []}
    python3 -m py_compile replay.py test_replay.py

Replay SHA-256: d5e23c6a4291b05014350454f68549428d2e9e1b80c5b72fa5e401f972841e1f.
Test SHA-256: bf0b629e3fe6cd3242c1a2c8ed7facc00d8c45342e513fc532b0952d30b065b1.

## Publication boundary

This is an inadequate probe matrix, not a semantic failure in a production interface. Because Docker stdout bytes were not durably captured at invocation time, the result is not a byte-reproducible runner package. Preserve as a failed T5 probe; do not promote it to PASS or merge as complete mutation-adequacy evidence. A successor run needs a pre-frozen executable, independent oracle, stdout-byte capture, and a concrete masking case before a one-shot Docker invocation.
