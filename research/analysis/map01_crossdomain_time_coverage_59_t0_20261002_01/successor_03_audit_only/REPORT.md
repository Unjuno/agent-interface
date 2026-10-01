# T0-03 audit-only result

Status: `PASS_AUDIT_CROSSDOMAIN_HOLD_REPRODUCED`.

This is one audit-only replay of the immutable T0-02 candidate result against
the six pinned historical inputs. The pre-run gate matched all five package
hashes, all six input hashes, and the predecessor freeze, candidate result,
run receipt, and failed-audit hashes. Five construction tests passed before
the audit. The first attempted test command from the parent directory failed
at Python import discovery before running tests; the documented invocation
from this allocation directory passed all five tests. It did not invoke the
candidate or change predecessor artifacts.

The sole formal auditor command was `python3 -B run_audit_only.py` (exit 0,
auditor invocations 1, retries 0). It independently reconstructed the sparse
event maps, found the expected v38 `post_control_score=1`, reproduced the
candidate summary, and found OpenTTD pointer button-down/up/neutral joins
`7/0/7`; observer records `263`, unique states `2`, transition index `[91]`.
No shared time/action link fields were found. Both source families still lack
per-press release evidence (`per_press_up=false`). The candidate's conservative
HOLD is therefore consistent with the raw historical record.

This result repairs the T0-02 auditor's absent-key-versus-zero defect; it does
not show physical held duration, useful feedback, recovery efficacy, safety,
human-tempo suitability, task completion, or MAP01 exit. No candidate, raw
experiment, app, model, GUI, OS input, Docker, WSL, GPU, or network experiment
was run in this allocation.

The initial parent-directory test-loader failure is retained in this report
for provenance. It was a command-context error only, not a test or audit
failure, and did not consume a formal audit invocation.
