# A01 — fail closed on a successful but non-neutral release query

## H / T / D / C / U

**H.** The #7847 owner candidate handles an exception from aggregate release reconciliation by latching a fault, but a successful aggregate query that reports a touched key still down may leave the owner active and admit another key under the same lease. The owner should fault and refuse further injection for either unresolved outcome.

**T.** A fake-display schedule presses F8 and F9. The fixture acknowledges F8-up but deliberately leaves F9 down when first released. The aggregate query returns successfully with `keys_down=[75]`. Then the same lease attempts `b`. Run the same regression against the exact #7847 base source, its published candidate, and a minimal patched candidate. Controls cover verified-neutral same-lease continuation and the already-handled aggregate-query exception. No native display or OS input is initialized.

**D.** Scoped construction PASS requires the exact #7847 candidate to fail the targeted assertion because it admits/injects `b`; the patched candidate must pass all three tests, reject `b` before injection, preserve `verified=false` and `keys_down=[75]`, retain fail-closed behavior for aggregate query exceptions, and allow normal same-lease continuation after verified neutral release. The parent source is also retained as a focused RED. Anything else is HOLD/FAIL for this candidate.

**C.** A non-neutral aggregate sample could reflect a stuck owner key or an external/foreign state; attribution is uncertain. Both interpretations require fail-closed admission because the owner cannot establish neutral input state. If a later clean reconciliation is desired, it must follow a separate explicit recovery contract.

**U.** This is a deterministic fake-display component test under Windows CPython 3.11.9. It does not exercise X11, OS input, the promoted controller/runtime, a GUI/game, useful feedback, bounded recovery, latency, safety in a real environment, or MAP01. It does not authorize or consume a live allocation. The regression is based on the #7847 v13 component candidate and is not evidence about every current-main path.

## Evidence

- Current main at intake: `3f24e85bff32a93fbc1ca244f7f249b843710743`.
- Parent of #7847: `e00c7f5e5c949095d40ade458355e55ea5990b9d`; exact owner blob `e7889a7a34fe76df5f230d4108a77055b105a680`.
- #7847 head: `e412e2e70f69183512b88e54d69a483dfa8589e4`; exact owner blob `df5c046eb55d81aa2ae6feb0a7bcf4fee9b07828`.
- Parent focused RED: one test fails because the second `down` raises nothing.
- Published #7847 candidate: 3 tests run, 1 intended failure; both controls pass.
- Minimal successor candidate: 3/3 pass. The fix latches the non-neutral-state `RuntimeError`, clears the active lease, then raises the same error. It does not change the retained partial unverified release record.
- The first harness runs had a bad exception-message regex; their original output is retained in `initial-*-harness-failure.log`. Corrected focused RED and GREEN outputs are separate files.

Reproduce with `./run.ps1`, then run `python -B audit.py`. The scripts use only Python standard library plus local file reads.