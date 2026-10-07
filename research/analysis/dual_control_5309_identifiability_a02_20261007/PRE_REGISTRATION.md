# Issue #5309 pairwise-identifiability A02 — PRE-RUN

Allocation: `5309-IDENT-A02-HOSTCPU-20261007`. Fresh successor allocation; A01 remains immutable and invalid. Main freeze: `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`.

## H / T / D / C / U

- **H:** Generic one-step entropy reduction and repeated success on a benign frequent branch can leave hidden states with incompatible safe commits observationally equivalent. An exhaustive bounded pairwise distinguishability oracle will identify each such pair and yield `UNKNOWN/YIELD`; information gain will not grant authority.
- **T:** Run a deterministic finite CPU-only model over: (1) four equally likely hidden states (`benign/hazard × mode 0/1`) where a one-step `probe_mode` reveals one bit but leaves same-mode benign/hazard pairs aliased; (2) five successful repeated `routine` observations on the same benign branch; (3) a pair with an admissible `witness` separator; (4) an otherwise equivalent pair with no admissible separator; (5) a separator that expires before its scheduled step; and (6) a null pair already separated in one step. Independently enumerate every common admissible action sequence through each horizon and compare the left/right observation histories. Record proposals, admission, execution and observation separately; rejected actions produce no observation. Keep the exogenous opportunity stream identical and independently score action-induced opportunity displacement against a no-action counterfactual.
- **D:** `PASS_METHOD_SCOPED` only if candidate and oracle inputs/hashes are frozen; generic information gain is exactly 1 bit while a safety-relevant same-mode pair remains aliased; five same-branch observations remain aliased; exhaustive oracle finds the separator and null controls, returns `UNKNOWN/YIELD` for no-separator and expired cases, never treats a refused action as executed/observed, never grants authority, and reconstructs opportunity displacement exactly. Mutation controls must reject equal-history false separation, missed valid separator, false expiry execution, refusal with an observation, and authority promotion. Otherwise `FAIL` or `HOLD` without rerun.
- **C:** Existing safe-probe/freshness/risk gates may suffice; this finite pairwise layer can be redundant or costly. Authored dynamics may overstate the frequency or relevance of benign aliases.
- **U:** Completeness applies only to the frozen finite states/actions/horizons. No global impossibility, nonstationarity, GUI transfer, live safety, task utility, latency, or product claim.

## Execution mode and boundary

Issue #5309 explicitly permits a deterministic no-model simulator without a container for its first rung. The required OrbStack inventory call currently fails on a containerd blob `operation not supported`; therefore this distinct CPU-only A02 uses Python stdlib on the host, with no network calls, GUI, model, GPU, input, or external effects. This does not claim OS-level network or resource isolation. Candidate and auditor are separate processes and independently authored implementations; the auditor reads the frozen fixture and raw only.

## Immutable predecessor

Do not rerun or edit A01. A01's `FAIL_AUDIT_CONTRACT_INVALID`, outputs, and report are retained at `dual_control_5309_identifiability_a01_20261007/` and linked to Issue #5309 / Draft PR #8265.
