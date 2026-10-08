# Issue #6138 T0b — reusable artifact value boundary

## H / T / D / C / U

- **H:** A surviving artifact may rationally change CONTINUE/SWITCH only when independent forward evidence establishes its applicability and consequence. An invalid/stale artifact must not receive that future value. Irrecoverable prior spend alone must not change the choice.
- **T:** Four deterministic recovery cards, exact fractions, three paired contrasts: sunk-only; independently verified reusable artifact; stale, nonapplicable artifact.
- **D:** `PASS_METHOD_SCOPED`. Candidate and independent auditor exited 0; auditor reconstructed 4/4 cards and 3/3 pairs, errors=[]. Baseline and high-sunk both select SWITCH (CONTINUE=4, SWITCH=5). Verified applicable artifact raises only CONTINUE's evidenced success probability to 9/10, yielding CONTINUE=8 versus SWITCH=5, so CONTINUE is selected. The stale artifact leaves forward success evidence unchanged and selects SWITCH (4 versus 5). Six construction tests passed, including planted stale-artifact value inflation and pair-label mutations rejected by the auditor.
- **C:** Formal candidate and auditor each ran once in separate OrbStack containers; retry=0. OrbStack Docker Engine 29.4.0, Linux/arm64, image `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; network none, read-only root and source, separate raw/output mounts, 0.5 CPU, 256 MiB, 32 PIDs, all capabilities dropped, no-new-privileges.
- **U:** Synthetic decision-oracle boundary only. No model/human behavior, actual artifact value, GUI effect, route/task benefit, safety or product behavior was tested. No T1 or live authority; no historical #57 evidence changed.

## Interpretation

The result distinguishes *past sunk expenditure* from a valid artifact's prospective contribution. The verified-artifact treatment legitimately changes a forward operand and may reverse the oracle choice. Merely retaining a stale artifact object does not establish future utility. This is a controlled method counterexample, not an empirical claim about any real recommender or model.

## Stop

T0b boundary discriminator complete. Any model-facing T1 requires a separate allocation with fixed model/version/settings, stateless balanced presentation, frozen response coding and independent review. The result does not authorize GUI actuation.
