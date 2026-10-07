# Finite outcome-set reversibility, T0 A01

Status: prospectively frozen, CPU-only finite-model experiment. No GUI, model,
user data, live application, external action, or runtime admission is involved.

## H / T / D / C / U

**H.** On the explicitly enumerated three-bit transition model below, a
certificate distinguishes (1) one recovery sequence that restores every
declared outcome, (2) complete recovery only with an outcome-conditioned
sequence, (3) at least one unrecoverable outcome, and (4) cases where evidence
does not support a recovery classification. It must reject a binary
`reversible=true` claim for the partial case while retaining the branching
positive.

**T.** Run the fixed six-case suite with the candidate and a separately
implemented exhaustive sequence oracle; compare classifications and retain raw
candidate traces, oracle traces, and a read-only audit. Include an incomplete
coverage mutation and a stale-receipt mutation. The model has three Boolean
state variables (`a`, `b`, `external`), two action schemas with two to four
declared outcomes each, two recovery operations, and a recovery horizon of two.

**D.** `PASS_METHOD_SCOPED` iff the independent oracle agrees on every complete,
fresh case; the uniform and branching positives retain their distinct labels;
partial and receipt-ambiguous negatives never receive a recovery certificate;
and incomplete/stale evidence is `UNKNOWN`. Any false certificate is
`FAIL_METHOD`; an inability to enumerate or audit exact model effects is
`UNCERTAIN`.

**C.** A static reversibility bit or the history-conditioned eligibility idea
in #7865 may already be sufficient. Real applications may make all symbolic
classes operationally irrelevant until an independent effect/recovery oracle
exists.

**U.** Outcome completeness, deterministic recovery effects, and the receipt
partition are authored assumptions. This cannot establish GUI observability,
permission, safety, actual compensation, application restoration, or an
unmodeled outcome probability. Labels are research classifications only.

## Frozen model and cases

State is a 3-bit tuple (`a`, `b`, `external`); the pre-action safe target is
`000`. Schema `edit` declares outcomes `100, 010, 110`; schema `submit` declares
`100, 010, 001, 111`. Recovery horizon is two operations: `restore_a` and
`restore_b`. Each case freezes the selected schema, outcome set, receipt class,
coverage/freshness and exact deterministic recovery transition table. State
`110` and `111` are traps under both operations; `001` is unchanged by both.

| Case | Schema / outcomes | Receipt | Expectation |
|---|---|---|---|
| uniform | edit: `100,010` | distinct | `UNIVERSALLY_UNIFORM` |
| branching | edit: `100,010` | distinct | `UNIVERSALLY_BRANCHING` |
| partial | submit: `100,010,001` | distinct | `PARTIALLY_RECOVERABLE` |
| ambiguous | edit: `100,010` | same class | `UNKNOWN` |
| incomplete | submit: `100,010,001,111`, coverage false | distinct | `UNKNOWN` |
| external write | submit: `100,010`, receipt invalidated by external write | distinct | `UNKNOWN` |

The uniform table makes both restore operations safe on the other outcome, so
the common sequence `[restore_a, restore_b]` restores both. The branching
table maps use of the wrong operation to trap `110`; each outcome has a
one-operation recovery when its receipt is distinguishable, but no common
sequence recovers both. The partial case has a declared outcome (`001`) with no
path to `000`. The ambiguous case uses the branching table but merges both
outcomes into one indistinguishable receipt class, so the required conditional
choice is unavailable. `external write` invalidates the receipt before any
recovery choice. The static baseline labels every case `true`; this is
intentionally overbroad.

## Provenance and reproduction

- Source base: `402c7d1b5147b2a905098f082233db60a47d68db` (`origin/main`,
  fetched 2026-10-05).
- Candidate, oracle, fixed inputs, runner and audit are this directory's files.
- A pre-freeze construction output is retained separately under
  `construction/`; it is not counted as the fixed run.
- WSLc was attempted for the fixed run, but image/container listing and image
  acquisition commands stalled without output. The candidate was not started
  in WSLc. The fixed run therefore uses the host's Python 3.12.10 on Windows
  10 build 26200.9550, single CPU worker, with no GUI, model, or network use.
  This is an environment substitution for a deterministic analytical test,
  not a WSLc result and not evidence of container isolation/resource limits.
- The fixed command and exact source digests are in `FREEZE.json`; the first
  fixed outcome is retained under `raw/` and must not be overwritten or retried.

The result is method evidence for this finite authored model only. It is not a
runtime feature or a claim about real-world interface effects.
