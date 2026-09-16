# Inkscape post-check selection race

Issue #383. Decision: **PASS_POSTCHECK_SELECTION_RACE**.

This direct successor to #371 keeps the same Inkscape 1.4 fixture, A-selection handle predicate, Right 20 ms effect and saved-SVG scorer. The single changed factor is whether an ordinary `Tab` changes selection A->B **after** the final A check has passed and before Right is sent.

Ten frozen first cases completed, five per condition. Every final check was A-positive with four dark-handle counts 176/176/176/176. Stable-after-check persisted A+2/B0 in 5/5. Switch-after-check persisted A0/B+2 in 5/5. Focus remained unchanged and pre/post/final physical key/button state was empty in all cases. Independent audit verified event order `final_check < postcheck step < effect_admit`, final-check pixels, saved SVG geometry, release and schedule, returning `PASS_POSTCHECK_RACE_AUDIT`, errors 0.

Therefore the #371 final screenshot/handle check is a useful precondition observation but not an atomic target binding. A selection transition after that observation can still redirect the effect. More screenshot polls can move the observation later but cannot by themselves make observation and effect one atomic operation.

H: post-check selection change can redirect Right. T: 10 serial cases, frozen source/schedule, ordinary XTEST, no model/game. D: PASS_POSTCHECK_SELECTION_RACE. C: a cooperative application-owned effect endpoint could validate selection and apply the effect in one semantic transaction; that mechanism is not tested here. U: deliberately injected ordering, one application/version/action/host, no natural incidence or general GUI claim.

Next single question: compare ordinary generic Right against a minimal cooperative effect-owner transaction that accepts `{expected_target=A, effect=Right}` and either applies to A atomically or refuses if current selection is B. Do not add more screenshot polling in that rung.
