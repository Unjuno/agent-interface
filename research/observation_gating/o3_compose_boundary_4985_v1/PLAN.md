# H/T/D/C/U — Issue #4985 O3 composition boundary

## H — hypothesis

The evaluator and standalone source-window verifier compare XIDs through `str()`; the live receipt adapter first uses Python equality against the trusted window XID, then calls the evaluator. For decimal-equivalent mixed `int`/`str` values, the two primitives therefore admit while the composed adapter refuses. Same-type matches admit. Python's `bool == int` and `float == int` edge cases are included to distinguish equality behavior from the evaluator's string comparator.

## T — test

One frozen local Docker run against main commit `7d1208cf323408897983ef2b5c75fd34f54d6815`. Exercise eight synthetic cases: same int, same string, int/string and string/int boundary pairs, unequal int and string negatives, bool/int, and float/int. For every case record direct gate, source verifier, and composed adapter output. The adapter fixture binds valid request, process, generation, focus, clocks, frame hashes, effect reference, and complete/current evidence. Xlib is stubbed to throw on any GUI access. A separate standard-library auditor validates all eight raw rows, exact reasons and source hashes, zero emissions/authority/GUI/model counts, and rejects five evidence mutations.

Container: pinned `python:3.12-slim-bookworm` image `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, linux/amd64, pull never, network none, read-only root/source, only fresh output mount writable, 0.25 CPU, 512 MiB, 32 PIDs, all capabilities dropped, no-new-privileges.

## D — decision

`PASS_COMPOSITION_BOUNDARY_SCOPED` requires all eight rows and the independent audit to reconcile; same-type positives admitted; decimal-equivalent mixed pairs admitted by both string-comparing primitives but refused by the adapter; all negative/edge controls fail closed; 5/5 mutations rejected. Otherwise preserve the exact failed result without a retry.

Interpretation: `HOLD_CALLER_TYPE_CONTRACT` until the normative XID representation and caller normalization contract are established.

## C — controls and alternatives

The transport capture constructs `source_window` with `int(trusted_window["xid"])`. The trusted-window caller may already normalize upstream. Adapter typed equality may intentionally enforce a schema contract; downstream string comparison may be compatibility behavior. The composed behavior alone does not establish a live bypass or a correctness regression.

## U — limits

Finite synthetic pure-function composition only. No real caller/JSON parser/X11/GUI/model/input/concurrency/latency/production behavior or exploitability claim. No runtime code changed. #4782's allocation and older evidence remain untouched. Formal execution is local Docker; GitHub records the preregistration and evidence only.
