# Issue #5993 T0 construction review — STOP before formal run

This is a construction-stage diagnostic, not a frozen or formal allocation and
not a claim about a live GUI, font renderer, application, or exploit.

## Current preparation checks

- Candidate self-test: 4 checks passed; 15 cases / 45 policy rows constructed.
- Independent raw auditor self-test: 9 checks passed.
- Python: 3.12.14.
- Unicode input files are pinned in `simulate.py` by SHA-256 and identify
  Unicode 18.0.0.
- Docker Desktop Engine was visible as running in its UI, but local `docker
  info` and `docker ps` did not return within 10 seconds. No container was
  started, stopped, removed, or otherwise touched.

These passing construction checks validate source plumbing and internal
consistency only; they do not validate whether the fixture represents the
Issue's rendered-label-to-resolved-identifier question.

## Boundary probe that blocks formalization

Probe: intended identifier `invoice.exe`; distinct resolved identifier
`invoice.` + U+202E RIGHT-TO-LEFT OVERRIDE + `exe`.

- Unicode 18 internal skeletons are equal.
- The existing corpus includes this pair only as
  `bidi_mismatch_unresolved`.
- Under that fixture classification, both `string_only` and
  `skeleton_warning_only` return `NO_MATCH`, no effect, and no warning.
- `exact_fresh_binding` denies the identifier mismatch, as expected.

Thus the simulator currently does not supply a positive rendered-alias
condition for this bidi pair. Its self-tests do not catch that omission, and an
independent auditor that accepts the same `unresolved` fixture would only
reconstruct the same assumption. This fails the precondition that T0 exercise
a declared display/identifier ambiguity. Do not interpret a candidate/auditor
PASS over the current 15-case table as method evidence.

## Required repair before any source freeze

Represent, independently and explicitly, (1) task's intended exact target ID,
(2) rendered/observed label, (3) app-resolved target ID, (4) freshness, and (5)
the effect target. Give the bidi pair a separately authored positive alias
fixture only if its display relation is supported by the declared rendering
semantics; otherwise label it unresolved and state that this T0 cannot test the
bidi class. Keep skeleton equality as a warning feature, never as authorization
or a substitute for the rendered-label oracle. The raw auditor must derive
expected rows from those independent fields and reject missing/contradictory
alias cases. Re-run construction checks after repair, then freeze exact source,
fixture, Unicode inputs, and decision gates before one formal run.

The construction was then revised before source freeze:

- Requested label, displayed label, intended ID, resolved ID, resolver rule,
  freshness, and the effect target are now separate fields.
- The authored bidi alias and other alias cases are represented as explicit
  fixture mappings. This states synthetic resolver/display semantics only; it
  does not assert a real glyph collision.
- String-only follows literal requested/displayed label equality. Skeleton
  equality only emits a warning in the warning-only policy; it never grants
  authority.
- The raw-only auditor independently reconstructs every label/ID/resolver field
  and tests mutation of the bidi displayed label and warning.

Repaired construction self-tests: candidate 8 checks over 15 cases/45 rows;
auditor 11 checks. These are still construction checks, not formal evidence.
At this point no formal candidate or raw audit has run. No GitHub source/result,
branch, PR, or Issue update has been created from this unfrozen preparation.
