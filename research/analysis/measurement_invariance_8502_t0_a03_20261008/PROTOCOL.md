# Issue #8502 T0 A03 — independent ordinal-screen successor

## H / T / D / C / U

- **H:** A deliberately coarse ordinal-response screen can flag large planted threshold, item-loading-pattern, and factor-structure shifts, accept an adequately sampled invariant control at predeclared margins, and return `UNCERTAIN` for a sparse sample.
- **T:** Fresh deterministic two-group, six-item, five-category fixtures: common one-factor control (F01); item-2 threshold shift (F02); item-2 loading reduction (F03); one-factor versus two-factor structure (F04); and a 20-per-group invariant sparse control (F05). Candidate and independently implemented raw-only auditor each run once, after source/input hashes are frozen. A03 uses seeds distinct from A01 and does not execute, patch, or relabel A01/A02.
- **D:** `METHOD_PASS_SCOPED` only if all five expected classifications/localizations match, all raw statistics reconstruct independently, all frozen source/input digests match, and each of six in-memory semantic/integrity mutations is rejected. Any discrepancy is `FAIL_METHOD`; any source/hash discrepancy is also a terminal audit failure. No retries or post-output fixes.
- **C:** The cases are authored synthetic distributions with large shifts and fixed parameters. A coarse moment screen can miss subtle item DIF, conflate real latent-distribution changes with measurement changes, and misclassify covariance patterns outside these fixtures.
- **U:** Synthetic screening only. No human responses, workload construct validation, ordinal CFA/IRT, scalar invariance, latent-mean comparability, accessibility, user benefit, GUI, model, runtime, or safety inference. `COMPATIBLE_SCREEN` is not permission to compare human means.

## Frozen construction and decision rules

Each response is an integer 0–4. The baseline cutpoints are `[-1.0,-0.3,0.3,1.0]`; ordinary factor loading is 0.80. F02 shifts all four cutpoints of item 2 in group B by +0.65. F03 lowers only item 2's group-B loading to 0.10 while preserving unit latent-response variance with independent residual noise. F04 changes group B to two independent factors, items 0–2 and 3–5. Full cases use 1,500 rows/group; F05 uses 20/group.

The screen first computes, for each item, `max_k |F_A(k)-F_B(k)|` at the **same ordinal cutpoint k** and flags threshold noninvariance only when that maximum is strictly greater than 0.15. This paired-cutpoint definition explicitly excludes A01's defective `max(F_A)-max(F_B)` estimator. If no item crosses the threshold margin, compute Pearson association changes on numeric ordinal scores; flag an edge only when its absolute between-group difference is strictly greater than 0.22. No changed edges means `COMPATIBLE_SCREEN`; three or more changed edges sharing exactly one item means `LOADING_PATTERN_NONINVARIANCE` localized to that item; every other nonempty edge set means `STRUCTURE_NONINVARIANCE`. Either group below 100 is `UNCERTAIN` before effect screening.

Truth labels and seeds are fixed in `config.json` before generation. Inputs and all source files, including this protocol, README, construction tests, candidate, auditor and freeze builder, are hashed into `FREEZE.json`. Construction tests are not formal candidate/auditor invocations. Candidate emits one `candidate.json`; auditor reads it once, recomputes raw statistics from frozen fixtures and runs six in-memory corruption controls. Candidate/auditor outputs are exclusive-create files; never overwritten.

## Execution boundary

Standard-library Python 3.12.10, local CPU, no network, model, GPU, GUI, participant data, WSLc/Docker invocation, or runtime code. The finite method itself requires no image boundary; WSLc is not used while its shared ownership/reconciliation gate remains open. No container capability or performance inference is made.
