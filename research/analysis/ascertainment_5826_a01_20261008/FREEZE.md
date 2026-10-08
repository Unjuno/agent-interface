# A01 — Oracle-known multi-channel ascertainment fixture

Status: pre-run deterministic method probe. Exact main base: `708ca59a8128f07fdb7e13a36704c6b2f79c9fb6`.

This is an additive, no-model test of Issue #5826's finite-fixture method. The frozen Issue protocol names a container. Docker/OrbStack image inventory is currently failing on a containerd content-store read (`sha256:8d984b04efe5bca7bd9b3808aac4f56bd273a6a1ada76cd51939253b874244ca`, `operation not supported`), so this A01 records a host-Python execution as a deliberate environment deviation. It can support only `PASS_METHOD_SCOPED_HOST`; the specified container T0 remains `HOLD_CONTAINER_TRANSFER`, not passed. No image was pulled or container started.

## H / T / D / C / U

**H:** In a closed, oracle-known synthetic frame with six fault classes, multiple detection channels, known source dependence, and an explicit UNKNOWN state, at least one plausible fault is missed by all ordinary channels while other faults are caught; an oracle-backed detection-vector audit exposes the blind spot, and a naive two-list capture-recapture diagnostic underestimates the known fault total under the declared dependence structure.

**T:** One deterministic candidate invocation builds 18 opportunities (two per fault class plus six no-fault controls) × four channel observations. Candidate reads only `fixture.json` (IDs, channel outputs, timestamps/dependencies), never the separate oracle sidecar. An independent auditor joins candidate rows to `ORACLE.json` by opportunity ID; verifies detection delays, false reports, UNKNOWN handling and dependence provenance; computes channel/union recall and two-list diagnostics; and runs five frozen corruption controls. No GUI, model, user data, external services, input, or application mutation.

**D:** `PASS_METHOD_SCOPED_HOST` only if the candidate emits all 72 channel/opportunity rows, the auditor reconstructs exact joins and the expected oracle-known fault classes, finds an all-channel-missed fault and a channel-exclusive detection, preserves one false report and UNKNOWN distinctly, calculates the two-list diagnostic without presenting it as a live hidden-count estimate, and rejects all five mutations. Any scientific/control mismatch is `FAIL_METHOD`; environment mismatch is separately recorded. `HOLD_CONTAINER_TRANSFER` remains until the exact finite method is executed in the container environment specified by #5826.

**C:** Oracle truth is known by construction; list detection dependence is explicitly planted in `fixture.json`, not statistically inferred from 18 opportunities. Capture-recapture values are diagnostic-only and are evaluated against the known synthetic total. An independent oracle is not a production log channel and provides no safety certificate.

**U:** This does not estimate real GUI incident prevalence, validate incident matching in a live product, establish channel sensitivity, or generalize to open populations, changing faults, unknown linkage, or faults outside this synthetic frame. Host execution does not qualify the requested container T0.

## Frozen identities and commands

- `fixture.json` SHA-256: `3114154c201a4d91f03607248fa5957ff2ba9f4be96b8c38f49840bbcbc3cd8d`
- `ORACLE.json` SHA-256: `f61d807d62e48745891edd7bedcb2f189e96b9346125272bda1d864034be7bd9`
- `run_candidate.py` SHA-256: `b146357926393bb2cc34f337f18d2579d37ed5c58ddd4663463840d8ede3a9da`
- `audit_result.py` SHA-256: `14227d89d529a52f27d723a55c98d71fa15e631a61ac17928242eccd05315ba5`
- `test_mutations.py` SHA-256: `a11cc9290500be46bdfdfcd0c74aaa1eddcf217d054cd95ab216e0ab7751c1ce`
- Candidate runtime: bundled CPython 3.12.14 on macOS 27.0.0 arm64; no network inputs.

Frozen invocations, from repository root:

```sh
/Users/taka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 research/analysis/ascertainment_5826_a01_20261008/run_candidate.py --out research/analysis/ascertainment_5826_a01_20261008/candidate.json
/Users/taka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 research/analysis/ascertainment_5826_a01_20261008/audit_result.py research/analysis/ascertainment_5826_a01_20261008/candidate.json
/Users/taka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 research/analysis/ascertainment_5826_a01_20261008/test_mutations.py research/analysis/ascertainment_5826_a01_20261008/candidate.json
```
- Candidate: `run_candidate.py`; auditor: `audit_result.py`.
- Run each exact command once from repository root with the bundled Python. Candidate output uses exclusive create; do not overwrite it. Auditor/mutation checks may read the retained output but must not rerun the candidate.
