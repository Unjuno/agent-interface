# A02 run record

- Issue #59 allocation A02 preregistered in comment 5987111555; refreshed-current-main freeze correction in comment 5987160510.
- Frozen current-main base: `81a59aed13492ba1d52ea80e03d48c3d8de7b2c5`; all eight source snapshots re-fetched at this SHA and byte hashes recorded in `PRE-RUN.json`.
- Candidate invoked once, exit 0. Auditor invoked once, exit 1. Retries: 0.

## Candidate observation

The candidate selected V15 through the pinned V39 `session_command` selector, installed release-batch backend v1 and Executor v13, and executed two fake-X cases. In both, the pre-sample observed keycodes 65 and 74; two UP attempts occurred at trace positions 15 and 19; keymap queries occurred at 12 (pre), 27 (post), and 34 (terminal cleanup), so none fell between the UP attempts. The post sample and release telemetry were at 28 and 30 respectively.

- Normal: post sample was empty. Both release rows classified absent at the post sample; terminal cleanup completed and fake held state was empty.
- Simulated lost SPACE KeyRelease: post sample retained only 65; SPACE classified still down and F8 absent. Terminal close failed closed with `owner release not verified: [65]`; fake server state retained 65.

## Auditor disposition

The sole frozen auditor failed 11 of 32 checks. Its per-case `rows` assumption did not filter `input_release_transition` from two earlier `input_admission` rows, so receipt/classification checks were applied to the wrong rows. It also required a nested `route.authority_claims` object omitted by the candidate, while top-level real-input/physical/application/real-X11 claims were false. Preserve `AUDIT.json` as FAIL. No auditor rerun or post-run edit occurred.

## Scope

This provides only a fake-server observation that the sample hooks fit before and after the exact selected-path release sequence without inter-UP keymap queries. It does not prove physical occupancy, X11 behavior, application effect, feedback usefulness, latency, recovery efficacy, threat control, or gameplay. The fail-closed cleanup error is not recovery success. Live allocation remains unassigned.
