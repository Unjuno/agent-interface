# ROADMAP — ACTUATION-EFFECT-CAUSAL-BINDING-20260918-001

## H
Time proximity between an exact input actuation receipt and an independently observed task effect is insufficient for causal self-credit under concurrent external effects. Requiring the effect receipt itself to bind the exact actuation_id, session, target, effect kind and causal order should remove false self-credit while preserving valid delayed self effects.

## T
- fixed synthetic input actuation receipt;
- candidate ACTUATION_BOUND join;
- independent history-replay oracle;
- TIME_ONLY <=500 ms comparator;
- excluded controls before source freeze;
- formal 4 immutable batches x80,000 =320,000 traces;
- balanced 10 families; no tuning/rerun.

## D
PASS iff candidate/oracle mismatch0; bound false-self0; valid self exact; external/other-actuation/conflict/mismatch/unordered/malformed fail closed; no-effect exact; TIME_ONLY false-self>0; authority promotions0; integrity/audit pass.

## C
Effect receipt authenticity is not proven; an application could forge actuation_id. Live transfer requires scorer separation.

## U
Standard-library synthetic causal join only; no GUI/X11/model/network/task input/live authority.

## STOP
One source-first batched result; no live transfer or repair mechanism here.
