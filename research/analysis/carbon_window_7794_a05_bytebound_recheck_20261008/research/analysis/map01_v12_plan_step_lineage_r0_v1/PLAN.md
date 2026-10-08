# MAP01 v12 plan/step lineage R0

Issue #1907. BASE `7f02687f8136ea6a390fc800900937adc227969c`.

This is a container-only integration-readiness contract. It composes two already-retained facts without rerunning them: current MAP01 v13/v3 carries release-batch `{identifier, step, position}` and explicitly non-authoritative physical status; retained v12/#996 carries authoritative confirmed physical DOWN/UP brackets with stable `{actuation_id, owner_id, intent_token, key}`.

The new factor is retrospective plan/step binding: a verified MAP01 ordinary-release row may label a v12 physical actuation only when its v12 UP bracket is nested inside the same outer release RPC and all owner/intent/key/batch identities agree one-to-one. The v12 DOWN inherits that plan/step only through the same stable actuation_id. No timestamp endpoint is changed and no authority is granted.

H/T/D/C/U are frozen in Issue #1907. One primary invocation only; reruns/replacements/tuning 0.
