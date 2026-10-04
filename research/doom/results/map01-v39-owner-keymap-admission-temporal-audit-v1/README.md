# C02 admission-to-keymap temporal audit successor

This additive package tests a missing contract in the retained C02 auditor: an
`input_admission` event is selected by token/key, but the C02 evaluator does not
validate `admitted_ns` or `input_ack_ns` against that occurrence's keymap sample
interval. The positive fixture in the predecessor test suite omits those fields.

`audit_admission.py` defines the occurrence-local temporal contract. Admission
and acknowledgement must be integer timestamps between the pre-down sample and
the down witness; the lease must still be valid through the down sample. It does
not claim physical key state, application consumption, useful task feedback,
recovery efficacy, or live-control performance.

Producer semantics were checked in the pinned predecessor source: the owner
records `admitted_ns` immediately before the XTEST key event and `input_ack_ns`
after `d.sync()` (`research/live_control/input_owner_v10.py`, lines 328–333).
Thus admission/ack belongs after the false pre-down witness and before the
true down witness in this harness.

Run the focused controls with:

```sh
python -m unittest discover -s research/doom/results/map01-v39-owner-keymap-admission-temporal-audit-v1 -p 'test_*.py' -v
```

The tests cover ordered positive input, missing timestamps, post-down admission,
cross-occurrence binding, and expiry before the down witness. The C02 candidate
and its historical audit are unchanged. This is host-side auditor-contract
validation only; no container, candidate, Xvfb, input, game, model, or formal
allocation was run. For comparison, the predecessor auditor's in-memory
`evaluate` function was called against the immutable C02 raw and a copy with
both admission timestamps moved after that occurrence's down witness. It
returned `backend_receipts_bind_each_occurrence=true` for both baseline and
mutation, and all overall checks remained true. The successor predicate accepts
the immutable raw and rejects the same mutation. This did not run the predecessor
auditor CLI or the frozen candidate. See `EVIDENCE.json` for pinned hashes and
the exact mutation.

Container gate: **STOP**. OrbStack/Docker 29.4.0 answered `docker version`, but
`docker image ls` failed because containerd could not open blob
`sha256:2775a09d208ff0d7c1f50490c45b62db929e87ba1dcbc3f2132ac71a704bcdd3`
(`operation not supported`). No image repair or container run was attempted.

## H/T/D/C/U and next roadmap step

- **H (hypothesis):** an audit that only joins admission by token/key can accept
  an admission timestamped after its own down witness; occurrence-local temporal
  checks should reject that mutation while accepting the retained raw.
- **T (treatment):** require `pre_down.finished <= admitted <= input_ack <=
  post_down.started`, ordered down/up sample intervals, and lease validity
  through the down sample.
- **D (data):** immutable C02 candidate raw at predecessor PR #7355 head
  `6ed0235da58ad849fc07daf75ce49a88ad46d407`, plus explicit synthetic positive
  and corrupted controls in `test_admission.py`.
- **C (controls):** 5 focused tests include missing timestamp, post-down
  admission, cross-occurrence token binding, and lease-expired-before-down
  negatives; the positive control checks the required temporal ordering.
- **U (uncertainty):** this checks evidence timestamps/logical X server samples
  only. It does not establish physical key-up, application effect, user-visible
  feedback, recovery, useful control, or live threat handling.

Roadmap: (1) have an independent reviewer compare this contract to the exact
producer semantics; (2) connect the validated predicate to the retained C02
raw and show baseline auditor acceptance versus successor rejection under
timestamp mutation; (3) only then propose integration into the owner PR or a
separately scoped successor. Live game/threat experiment remains independently
gated and is not replaced by this audit work.
