# r133 cross-domain time-coverage audit-only successor T0-03

Allocation: `R133-CROSSDOMAIN-TIME-COVERAGE-59-T0-20261002-03-AUDIT`.

## H / T / D / C / U

- **H:** The T0-02 candidate's conservative cross-domain HOLD is source-consistent; the second audit failure is a sparse-event-count zero-default defect, not a trace mismatch.
- **T:** Audit-only replay of the immutable T0-02 candidate result against the same six frozen inputs. Independently parse raw source counts, analysis/raw SHA joins, OpenTTD button-down/up/neutral joins, AIT observer state transitions and candidate summary. No candidate or raw experiment reruns. One raw-only auditor invocation; retries zero.
- **D:** `PASS_AUDIT_CROSSDOMAIN_HOLD_REPRODUCED` only if absent event classes count as zero, v38 `post_control_score=1`, candidate event maps exactly match raw maps, observer rows=263/states=2/transition=[91], button downs/ups/neutral joins=7/0/7, all coverage/effect/occupancy claims remain HOLD, and every input/candidate-result hash matches freeze. Mutation tests must reject nonzero/forged count changes and candidate overclaims.
- **C:** Predecessor T0-01 and T0-02 files/results remain unchanged. This allocation reuses T0-02's single candidate result by exact SHA; it performs zero candidate executions. Six historical inputs remain pinned and match current main at freeze.
- **U:** This is only an audit of historical record classification and the HOLD decision. It does not establish physical held duration, useful feedback, recovery efficacy, safety, human tempo, task completion or MAP01 exit.

The run is audit-only; no live app/game/model/GUI/input, Docker, WSL, GPU or network call is part of the test.
