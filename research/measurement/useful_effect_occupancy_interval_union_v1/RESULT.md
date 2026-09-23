# #1328 interval-union occupancy result

Decision: **PASS_OCCUPANCY_INTERVAL_UNION_EQUIVALENT_SCOPED**

One frozen logical formal invocation, reruns/replacements/tuning0.

## Evidence

- exhaustive bounded language: **50,730** cases; old-set mismatch0; independent pointwise mismatch0;
- deterministic bounded random: **500,000** cases; exact old #988 set implementation mismatch0;
- independent pointwise cross-check: **25,000** random cases; mismatch0;
- nanosecond stress: **100,000** cases over50–500 ms windows and absolute timestamps in the10^14–10^15 range; invariant errors0;
- maximum Python allocation observed by tracemalloc in an ns stress batch: **16,292 bytes**;
- exact parent #988 candidate Git blob: `0482cf4c08b8c04d524a3eac11b798f07f0e0524`;
- replacement helper source contains no calls to `range`, `set`, or `frozenset`;
- independent audit PASS/errors[]; corruption controls5/5.

Result SHA-256: `e56b1989582bcb043d2c2082e17785f232c919bf5b90470565a2895398659d6d`.

## Scoped conclusion

The #988 occupancy tuple can be computed with interval unions without changing its integer half-open semantics on the tested corpus. The retained raw-ns live hang localized by #1325 is therefore avoidable without changing effect classification or occupancy meaning.

This does **not** relabel #1325 and does not itself prove the live causal-effect chain. A subsequent live allocation may substitute only this proven-equivalent helper into the exact causal-effect science path and must receive a fresh #60 lease.
