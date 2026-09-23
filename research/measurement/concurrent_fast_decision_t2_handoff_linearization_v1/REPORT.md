# #1463 T2 handoff linearization — retained formal result

Task: `CONCURRENT-FAST-DECISION-T2-HANDOFF-LINEARIZATION-A10-20260918-013`

Decision: **`PASS_T2_HANDOFF_LINEARIZATION_SCOPED`**.

## Question

#1449 exposed a measurement/authority ambiguity: the transport receive call may return at raw clock `R`, while a later mutex acquisition produces a reported clock `P`. A local commit `C` can satisfy `R < C < P`; calling `P` the receive time hides a real post-transport-return admission.

This successor changes one contract factor only. It separates:

- `raw_recv_return_ns = R`: transport telemetry;
- `authority_publish_ns = P`: the unique authority handoff linearization point;
- `commit_ns = C`: final local admission clock.

Publication and final admission serialize on the same authority critical section. `R < C < P` is retained explicitly as `BETWEEN_RAW_AND_PUBLICATION`; it is not called pre-raw and is not claimed post-authority. `C >= P` must refuse.

## Frozen formal

One deterministic formal invocation, seed `146120260918013`, reruns/replacements/tuning `0/0/0`.

- histories: **250,000**;
- forced `R<C<P`: **60,000**;
- forced `P<C`: **60,000**;
- candidate/oracle full result+state mismatch: **0**;
- admitted effects with `C>=P`: **0**;
- stale-generation effects: **0**;
- `R<C<P` rows classified `BETWEEN_RAW_AND_PUBLICATION`: **60,000/60,000**;
- fresh pre-publication CLEAR effects: **100,000**;
- ordinary-authority-false effects: **0**;
- HARD effects: **0**;
- wrong-scope effects: **0**;
- future/forged-generation effects: **0**;
- replay second effects: **0**;
- duplicate-publication double advances: **0**;
- delayed-reported-receive discriminator hidden-after-raw effects: **60,000**.

The discriminator result is the key measurement finding: if `P` is mislabeled as receive, all 60,000 `R<C<P` effects appear “pre-return” even though transport receive has already returned. The candidate preserves both clocks and therefore does not launder that interval into a stronger authority claim.

## Integrity

Independent audit decision matches the formal decision. Seven copied-result corruption controls all reject their mutations. Postformal source SHA-256 values match the frozen manifest exactly.

- formal result SHA-256: `0915ed0e46f8b2a257ea3fa5b8224704b8a750e0cc4d81aa04597f47a47ed77b`;
- audit SHA-256: `86e3c0861dc3e6b109c749001d436ba9dc8587366c4fd3d42d959bafd47ab203`;
- deterministic ledger SHA-256: `9ba95ecbe51fec9591dcf320b21624051f2bcb946434f600c02d02bc8c16776c`.

A preformal remote-readback check had found that the initial uploaded `runner.py` omitted three comments only. Formal was still 0. Remote executable bytes were adopted as canonical, the local copy and manifest were normalized before source freeze, and no semantic logic, seed, corpus or gate changed. That event is retained in `SOURCE_FREEZE.json` rather than hidden.

## Interpretation

The scoped result supports an explicit two-event contract: transport receive and authority publication are not the same event unless the implementation makes them the same linearization point. If authority publication is the boundary, all admission claims must be made relative to `P`, while `R→P` remains separately observable telemetry.

This does **not** show that an arbitrarily large `R→P` delay is acceptable. A stricter runtime can choose raw receive `R` as the authority boundary only if `R` itself is made globally linearizable with final admission.

## Boundary

Synthetic standard-library state/concurrency semantics only. No provider/model call, network, GUI/X11 input, physical cancellation, task usefulness, MAP01, token, human-tempo or production-runtime claim. Receipt draining remains separately owned by #1459; later-generation ABA is separately owned by #1460.
