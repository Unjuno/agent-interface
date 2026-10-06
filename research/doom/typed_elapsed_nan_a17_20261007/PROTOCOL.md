# Typed elapsed metadata: bounded engineering qualification

Issue #8249, parent #59. Intake main 5d48c8beb7e0380da4ab3e15cc93cde111d74749.
Only additive evidence; the tested one-line patch is NOT applied to shared code.
Full original module and its full in-repository dependency retain exact Git identities.
No old GUI/Tk experiment or denied publication is reused.

## H / T / D / C / U

H: A negative out-of-tolerance test admits NaN; a positive consistency requirement
rejects it while preserving finite outcomes. Actual freshness still uses integer ns.
T: One 48-row synthetic matrix: twelve duration tokens, two decision ages, two
JSON decoders. Per row compare complete original/candidate modules then the exact
existing action-validity evaluator. Strict decoding refuses three nonstandard
constants before module invocation. No captures, native input, model, game or GPU.
Run in the supplied private Linux/CPython3.13.5 container with installed Pillow12.3.0.
Engine/image attestation and shared-workstation resource allocation are absent.
Command: python -B run.py results/raw.json (fresh output only; timeout20s).
Independent command: python -B audit.py results/raw.json --controls.
D: 48 rows, all expected decoder/module/freshness outcomes and source hashes;
NaN changes ONLY permissive snapshot acceptance; finite positive and negative
controls agree; stale accepted snapshots remain rejected; no authority grant;
six byte-effective well-formed mutations rejected. Contradiction=FAIL;
incomplete source/output/process=HOLD/STOP; no rerun or gate tuning.
C: Hand-authored synthetic events, not a claim that a real producer emits NaN.
Default Python JSON supports nonstandard constants; strict JSON does not.
U: Full V39 startup, clock calibration, live threat control, arbitrary numeric
magnitudes/objects, physical release, user tasks and speed/tokens remain untested.
Same-author separate-process auditor is not independent human review.

## Variables and units

| Symbol/code | Meaning | SI unit | Definition | Domain/assumption | Type |
|---|---|---|---|---|---|
| capture_ns | capture timestamp | s, represented in ns | supplied integer capture instant | synthetic nonnegative integer | scalar integer |
| ready_ns | typed-result ready timestamp | s, represented in ns | supplied ready instant | ready at or after capture | scalar integer |
| elapsed_ms | claimed extraction duration | s, represented in ms | tested input field | valid: finite int/float, not bool; invalid controls explicit | scalar number or labelled invalid value |
| derived_ms | reconstructed duration | s, represented in ms | (ready_ns-capture_ns)/1e6 | same clock domain | scalar number |
| tolerance | preserved consistency tolerance | s, represented in ms | 1e-9 ms | original code threshold, not calibrated accuracy | scalar real |
| age_ms | decision age from capture | s, represented in ms | 50 or 200 | synthetic, budget100ms | scalar integer |

Unit check: one millisecond contains 1,000,000 nanoseconds, so subtracting
same-domain ns timestamps and dividing by1e6 yields ms. The comparison is
between two ms values. The tolerance is NOT a physical measurement claim.

## Argument and check

For finite absolute difference, exactly one of greater-than-tolerance and
less-than-or-equal-to-tolerance holds; negating the latter preserves rejection.
For NaN both ordered comparisons are false, so the old rejection is false
but the new negated-consistency rejection is true. Type checks still execute
before subtraction; infinity fails consistency. No freshness threshold changes.
This reasoning does not establish handling of arbitrary huge integers or live
emission. The selected near-boundary decimals are away from binary64 rounding
ambiguity; the independent Decimal oracle checks the frozen wire values.

## Roadmap and review

RED six methods (one intended failure) -> one-line candidate/GREEN six methods ->
public source/patch/gate readback -> one48-row invocation -> independent audit and
six controls -> additive evidence PR -> actual review/check gates -> permitted
main integration/readback. No self-approval, synthetic agreement or bypass.
No branch deletion while review or evidence custody depends on it.

## Primary context

Python3.13 json manual: https://docs.python.org/3.13/library/json.html
Python comparison manual: https://docs.python.org/3.13/reference/expressions.html
These document default nonstandard constants and unordered NaN comparisons.
