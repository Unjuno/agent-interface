# Issue #6045 T0 — opportunity-conditioned age of actuated information

Status before invocation: preregistered synthetic method test; no live model/application authority.

## H / T / D / C / U

**H.** Delivery-AoI or onset→effect latency alone can mis-rank routes: a newer delivered observation may be followed by a late relevant effect, while a route with higher delivery age has a timely relevant effect. Equal onset→effect can also conceal different source-to-effect age and source validity. The proposed card must not reset on motor pulses, dispatch, unrelated effects, or observations merely shown to a model without attributable use.

**T.** One finite 18-row no-model event fixture; one candidate invocation; only after exit 0, one independent raw-only auditor invocation; retries 0. It includes two paired ranking witnesses, eight original edge cases, and six measurement-identity refinements: bounded timestamp intervals, effect-before-source, unrelated opportunity, multiple shown observations without use attribution, an offset-uncertain cross-clock relation that can reverse order, and an interval-straddling deadline. The auditor reconstructs all rows and rejects omission, ID/source swaps, removed effects, and clock-comparability corruption.

**D.** PASS_METHOD_SCOPED only if the candidate and independent enumerator agree on every frozen case, both planted ranking inversions are detected, only a relevant effect resets the declared opportunity, and no scalar age/order/timeliness is emitted when lineage or clock precedence is unproven. Exact timestamps produce degenerate intervals. Any candidate/auditor disagreement or mutation false-acceptance is FAIL_METHOD; source/image/fixture identity mismatch or unavailable execution gate is STOP, not scientific failure.

**C.** Synthetic times use a declared monotonic millisecond axis. Interval age `[e_lo-g_hi, e_hi-g_lo]` is computed only after strict source-before-effect proof (`g_hi < e_lo`). ON_TIME requires `e_hi <= deadline`; LATE requires `e_lo > deadline`; overlap is UNKNOWN. A declared single-source lineage is fixture truth only, not model causal-use proof.

**U.** This experiment cannot establish actual GUI/game/model behavior, real ancestry, task benefit, safety, human tempo, or production scheduling value. No live application, GUI/input, game, model, GPU, or external network is involved.

## Frozen execution contract

- Main at preparation: `39cff8c45e3df04f1f7e98962b043c3fb0179ed2`; additive branch `research/opportunity-conditioned-actuated-info-6045-t0-20261002`.
- Source path: `research/analysis/opportunity_conditioned_actuated_info_6045_t0_20261002/`.
- Image: `python:3.12-alpine@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b`, platform `linux/arm64`; exact local image ID checked before run.
- Candidate container: no network, read-only root/source, output-only writable bind, 0.5 CPU, 256 MiB, 32 PIDs, non-root, `--rm`, unique name. Auditor uses the same limits; raw output bind is read-only.
- No image pull/build, no container/VM inventory inspection, no modification of pre-existing resources. Candidate once; auditor once only after candidate exit 0; zero retries.

## Outcome

Pending container candidate and independent audit. Do not infer success from host construction tests.
