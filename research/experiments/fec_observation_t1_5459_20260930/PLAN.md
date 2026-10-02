# T1 — deterministic fountain-style repair versus retransmission

## H — hypothesis

On matched deterministic packet-loss/delay traces, proactive fixed repair can
reduce time-to-usable observation windows versus retransmission when a source
symbol is erased, while adaptive repair can avoid fixed-repair overhead on a
clean window. A generation/window/dependency/integrity gate must prevent
false semantic completion.

## T — bounded experiment

Pin current main `6a1e2f16762b1a2ace7347a282f7ad6d12c7a0fe`, issue #5459's T0
raw SHA `9F8D429FA3311E5BF94343CC3AC5F5050E2ABF2865AF3F77760CBEF5E9028B9A`,
and the current issue protocol. Model four source symbols in two XOR repair
pairs. Compare systematic retransmission, two fixed proactive parity symbols,
and feedback-driven adaptive repair on the same 64 six-slot erasure masks
crossed with eight frozen binary delay profiles: 512 traces, 1,536 arm runs.
Feedback cut is round 1; deadline is round 4. Then inject whole-window wrong
generation, wrong window, incomplete dependency manifest, stale manifest hash,
and one unauthenticated corrupted source packet for all three arms. Retain
packet-level raw rows and have a separate auditor re-decode the equations.

This is a deterministic host construction because #5085 has no fresh named
container allocation; do not invoke Docker/OrbStack. No model, GUI, X11, MAP01,
or external observation source is involved.

## D — decision gate

`PASS_T1_DETERMINISTIC_TRANSPORT_CONSTRUCTION_ONLY` requires all 512 matched
traces per arm, fixed repair completing earlier than retransmission on every
single-source-erasure/no-delay trace with both repair slots available, adaptive
repair using fewer transmissions than fixed repair on the clean trace with the
same completion round, zero false semantic successes across all injected
faults, and independent audit agreement for every recorded packet/decoded
window. Any false semantic success or audit mismatch is FAIL; an incomplete
trace grid or source/hash mismatch is STOP.

## C / U — limits

The XOR code and binary deterministic channel are small construction models;
they do not estimate RaptorQ performance, real network latency, burst-loss
frequency, or production transport reliability. The authoritative expected
window state is an explicit simulator oracle. A pass does not validate real
observation freshness, physical action occupancy, task effect, human tempo, or
MAP01 recovery coverage.
