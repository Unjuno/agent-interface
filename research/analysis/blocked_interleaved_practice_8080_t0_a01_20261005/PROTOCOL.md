# Issue #8080 T0 A01 protocol

## H / T / D / C / U

**H.** A deterministic blocked/interleaved schedule generator can expose the
same three reversible procedure variants with exactly equal per-variant
attempts and feedback counts, while changing only practice order; an independent
oracle can distinguish valid, wrong-target, false-success, and out-of-family
traces.

**T.** Generate two schedules over three training variants, four attempts per
variant, and two auditor-only held-out variants. Blocked order groups all four
attempts of each procedure. Interleaved order cycles through all three variants
four times. Each scheduled task emits a reversible in-memory state change and
its inverse. The independent auditor reconstructs both schedules and checks
exact dose, task identity, the held-out boundary, effect truth, reversal, and
scoring controls. Mutation controls alter exposure, duplicate an attempt, leak a
held-out ID, forge a forward effect, and break an inverse.

**D.** `METHOD_PASS_SCOPED` requires exact schedule reconstruction; equal
attempt and feedback counts; all three variants in both arms; the declared
blocked/interleaved ordering; zero held-out leakage; correct forward and inverse
effects; and rejection of all five mutations. Otherwise retain `FAIL` or
`HOLD`. T0 cannot establish any human-learning effect.

**C.** The cyclic interleaved order may add spacing and switching costs along
with contextual interference. A short synthetic task family cannot separate
those mechanisms or predict the better human schedule.

**U.** No people, model, GUI, app state, delay, retention, transfer, burden,
accessibility, or safety outside a pure in-memory fixture is tested. A future
study still requires separate consent, privacy/ethics review, preregistration,
and coordination with the owning #8080 and related #8084 study.

## Frozen design

`design.json` fixes three practice variants, four exposures each, identical
training facts and feedback, and the two orderings. `scorer_fixture.json`
contains the held-out set, independent expected effects, and negative scorer
traces; it is not read by `candidate.py`. Each forward flag set is followed by
an inverse flag clear that restores the initial false state. These are synthetic
safe labels, not real GUI actions.

## Execution boundary

The scheduler contract is deterministic and has no OS or GUI dependency. This
host run does not claim OrbStack container validation. The same-session
OrbStack image preflight for #8084 failed on containerd image-content access;
no daemon repair or image pull was attempted. Any later container run needs a
fresh supported image preflight and must retain that separate runtime evidence.
