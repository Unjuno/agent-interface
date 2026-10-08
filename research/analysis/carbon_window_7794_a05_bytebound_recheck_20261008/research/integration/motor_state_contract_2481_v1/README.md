# Planner-facing MotorState contract gate (#2481)

H: commanded/observed motor state can be exposed without authority promotion.
T: validate bound records for confirmed input, explicit uncertainty, retained release transitions, missing bindings and forbidden authority fields.
D: seven deterministic cases with expected accept/reject and reasons.
C: pure standard-library contract audit; no GUI, input, model, lease mutation or application-effect claim.
U: this is a prerequisite for a runtime adapter, not a promoted public API.
