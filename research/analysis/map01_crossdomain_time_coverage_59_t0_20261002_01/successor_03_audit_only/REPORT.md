# T0-03 audit-only result

Status: `PASS_AUDIT_CROSSDOMAIN_HOLD_REPRODUCED`.

This is one audit-only replay of the immutable T0-02 candidate result against
the six pinned historical inputs. The pre-run gate matched all five package
hashes, all six input hashes, and the predecessor freeze, candidate result,
run receipt, and failed-audit hashes. Five construction tests passed before
the audit. Pre-audit setup had three command-context errors: the first
test-loader invocation ran from the parent directory and failed Python import
discovery before any test; two hash-gate shell invocations resolved the input
path relative to the wrong directory and stopped at file-not-found. The
documented test invocation and hash gate with explicit parent-relative paths
then passed. These setup errors invoked neither candidate nor auditor and did
not change predecessor artifacts.

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

All three initial command-context failures are retained here for provenance;
they were not candidate/test/audit failures and did not consume a formal audit
invocation.
