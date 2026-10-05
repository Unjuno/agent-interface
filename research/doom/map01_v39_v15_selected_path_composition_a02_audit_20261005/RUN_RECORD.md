# A02 audit run record

- Issue: #7921; parent Issue #59; allocation `V39-V15-COMPOSITION-A02-AUDIT-20261005-01`.
- Freeze commit: `53921484f64ff3eb85369c3ba7a01f94e0c8f1ac`, based on intake main `190100f7c9acb2bfc5618d1621761a0329b368eb`.
- Candidate/runtime invocations: 0. Auditor invocations: 1. Retries: 0.
- Frozen auditor: `audit_v2.py`, SHA-256 `6413a188856dfed755cc19886bd12c83e076c79b873d8df697422712577a6954`, blob `5a09da9351b58dcc0b255c1bfb8fd91aaa418149`.
- Frozen raw input SHA-256 matched: `d4b65dd6b8a32e64b0f001293e6ad606c0ed95c8d454392adf6028791736203d`.
- Frozen predecessor audit SHA-256 matched; its recorded status remained `FAIL`.

## First outcome

The sole invocation produced raw timeline reconstruction 27/27 and rejected all six in-memory mutations. However, the launch wrapper passed the A02 package's own `PRE-RUN.json` (SHA-256 `b40c07f2387cabe9f695ba5a95a45f63840ce6ec832d6cc2adb6ab1e3422f4da`, blob `55f8ecfb60bf7dab724fdab7e492fe484e80a574`) as the auditor's second argument. The frozen command requires the copied A01 `inputs/a01_PRE-RUN.json` (SHA-256 `b3155f73c70373cf0d341f19ef6d6ccdbe709e6033f322ddaa51330ec448268f`, blob `99fc2413d3ebcb4480ed97386c7b4f00713a6fd6`). Therefore the auditor reported `FAIL` with `pre_run_sha256_mismatch`, `pre_run_provenance_mismatch`, and `pre_run_source_binding_incomplete`. Formal disposition: **STOP_PROTOCOL_INPUT_MISMATCH**; provenance gate not evaluated on the pinned A01 freeze. The host wrapper process itself exited 0 because it printed the auditor result without propagating the internal status; that exit is not a PASS.

## Exact invocation binding

One CPython 3.14.5 `python3 -c` process compiled the frozen source blob in memory and called `run(raw, pre_run, audit_v1)`. Argument mapping was:

1. source: frozen `audit_v2.py` blob above;
2. raw: `inputs/a01_candidate.stdout` blob `99b8d18ceb9a264ce4c01cbc1aaaf866fb3af4a2`;
3. **wrong input:** A02 root `PRE-RUN.json` blob `55f8ecfb60bf7dab724fdab7e492fe484e80a574`;
4. A01 `inputs/a01_AUDIT.json` blob `c6066ef6430c46355bc08f4c2c86130b935e0da7`.

The exact stdout is preserved in `AUDIT_V2.stdout`. No candidate ran. No rerun, source edit, or replacement result was made after the first outcome.

## Environment and scope

Docker Engine 29.4.0 was reachable, but read-only `docker image ls` failed on content-store blob `sha256:0e35cdb51a82e59d359ec09b85ce835d9217a1eab65b68ce1871c9b0a85014c9` with `operation not supported`; no pull, repair, restart, or substitution was attempted. The one host audit has no container-specific semantics.

A02 is a protocol/input-binding STOP. It does not change the original A01 audit FAIL and establishes no real X11, physical key state, application effect, useful feedback, latency, recovery, threat response, or gameplay result.
