# Issue #5593 addendum — post-success collateral follow-up T0

Allocation: `POST-SUCCESS-COLLATERAL-5593-T0-20261002-01`

## H / T / D / C / U

- **H:** A frozen finite ledger can retain the original first-terminal verified-success fraction while separately distinguishing clean success through two declared observation horizons, observed delayed collateral, pending follow-up, and lost follow-up. A success receipt alone must not certify cleanliness beyond the observed horizon.
- **T:** Five synthetic launched episodes, same task-contract label and time origin; 3 and 6 tick follow-up cutoffs from launch. Cases: verified success then delayed collateral, verified success with complete clean follow-up, success then administrative follow-up loss, verified failure, and policy safe-stop. Candidate sees only the declared event ledger; independent auditor reconstructs from raw rows. Candidate once; raw-only auditor once; retries 0. Run in a pinned local Python container with network disabled, read-only source mount, bounded CPU/memory/PIDs, output-only writable mount.
- **D:** `PASS_METHOD_SCOPED` only if (a) the first-terminal outcome counts/fraction are unchanged by post-success events, (b) horizon statuses and all-launched lower/upper clean-success fractions match independent replay, (c) follow-up loss never becomes “clean,” and (d) corruption controls reject missing episodes, false clean claims, and retroactive rewriting of first-terminal success. This does not test the empirical hypothesis.
- **C:** If actual task contracts do not care about effects after the first success window, the extension adds no decision value. A complete independent final-effect oracle may already include the relevant collateral window.
- **U:** Hand-authored finite records only. No task-family contract, real delayed collateral, GUI observation, route/model behavior, causal quality, safety, or indefinite absence is established. `NO_COLLATERAL_COMPLETE` applies only through the explicit cutoff; it is not “no collateral ever.” Administrative-loss intervals are illustrative, not an empirical censoring assumption.

The original #5593 first-terminal estimand and its artifacts are not modified. This is a separate synthetic multistate/horizon accounting control, not a rerun of its competing-risk calculation.
