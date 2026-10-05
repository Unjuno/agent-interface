# T3 STOP — incomplete finding-sensitivity mutation

Allocation `OWNER-KEYUP-TIMESTAMP-ORDER-5156-T3-20261004-01`, frozen on main `2f72c6474167f93a2e1a6e2b8a497a1a8a6d266a` and preregistered in Issue #5156 comment 5975334727.

- Candidate: exactly one invocation, exit 0. All four analyzer rows reported `measurement_ready=true`.
- Auditor: exactly one invocation, exit 1. It separated the two expected scientific mismatches from raw integrity, producing `FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED` and identifying both malformed-order cases. Three of four mutation controls rejected.
- Failure reason: the frozen classification mutation changed only `ack_before_admission` from ready to not-ready. The other malformed case still kept the aggregate hypothesis disposition at FAIL, so the mutation control incorrectly treated that edited output as undetected.
- Retries: zero. No candidate or auditor was rerun.

Disposition: `STOP_AUDIT_MUTATION_SENSITIVITY`. T3 raw and first audit output remain unchanged. The raw plus the independent classification in the first auditor output point to the same finding as T2, but the incomplete audit mutation gate means neither allocation is promoted to a qualified result. A successor must preflight a mutation that changes the aggregate disposition (both negative rows together), then use a new allocation/path.
