# A02 independent audit protocol

Issue #7921, parent #59. The consumed A01 candidate allocation is not repeated. This audit runs only on the immutable A01 stdout, PRE-RUN and failed AUDIT inputs copied below.

## Frozen inputs

- A01 commit: `eddd393a504c33f246889279aee80785560ac4c6`
- Candidate raw: `inputs/a01_candidate.stdout`, SHA-256 `d4b65dd6b8a32e64b0f001293e6ad606c0ed95c8d454392adf6028791736203d`, source Git blob `99b8d18ceb9a264ce4c01cbc1aaaf866fb3af4a2`.
- A01 PRE-RUN: `inputs/a01_PRE-RUN.json`, SHA-256 `b3155f73c70373cf0d341f19ef6d6ccdbe709e6033f322ddaa51330ec448268f`, source Git blob `99fc2413d3ebcb4480ed97386c7b4f00713a6fd6`.
- A01 AUDIT: `inputs/a01_AUDIT.json`, SHA-256 `78452bbb59c65112622bea194c02eb98c83601148c24b3a68fcc47a3ffcdfb51`, source Git blob `c6066ef6430c46355bc08f4c2c86130b935e0da7`.
- Independent auditor `audit_v2.py`: SHA-256 `6413a188856dfed755cc19886bd12c83e076c79b873d8df697422712577a6954`, Git blob `5a09da9351b58dcc0b255c1bfb8fd91aaa418149`.
- Auditor source and all three inputs are committed on the additive branch before the sole invocation.

## Frozen command and gates

Command for a checkout of this package:

```sh
python3 audit_v2.py inputs/a01_candidate.stdout inputs/a01_PRE-RUN.json inputs/a01_AUDIT.json
```

The auditor verifies exact input SHA-256 values, A01 base/attempt provenance and the retained predecessor `FAIL`; then independently checks the JSON trace's event positions, no inter-UP keymap query, pre-sample owner-state ordering, later cleanup ordering, release-row/receipt identity, sampled-empty states, terminal-empty state, and explicit non-authority claims. It runs six in-memory mutations inside this single auditor invocation: inter-UP query insertion, sample-before-owner-state reordering, removed release row, nonempty sampled state, wrong receipt keycode, and omitted terminal cleanup query. No candidate is invoked.

Disposition `PASS_AUDIT_V2_RAW_RECONSTRUCTION_ONLY` requires all baseline checks and all six mutation rejections. A failure is retained without retry or source edit.

## Scope / competing explanation / uncertainty

This is a raw-trace chronology audit only. PRE-RUN's source bindings are checked as metadata; source modules are not loaded or independently re-executed. It cannot prove real X11/physical key state, application consumption, useful feedback, latency, recovery, threat control, gameplay, or full V39 startup. XSync means server synchronization only. The original A01 `AUDIT.json` remains FAIL regardless of this audit.

Docker Engine 29.4.0 image inventory stopped on a content-store blob with `operation not supported`. This stdlib JSON audit has no container-specific semantics, so one host Python 3.14.5 audit is the frozen fallback; do not repair or restart the shared engine.
