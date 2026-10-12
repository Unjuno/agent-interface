# #8879 assumption-gated policy selection — A01

Status: prospectively frozen finite-method experiment; not yet run.

## H / T / D / C / U

- **H:** When exact adaptive diminishing returns fails, a bounded two-step policy can have positive decision-value where myopic greedy stopping has none; checking the property can therefore select a better bounded policy on this finite family.
- **T:** Enumerate four equiprobable worlds `(left_bit, right_bit)`, with the required decision equal to XOR. Two deterministic observations reveal one bit each. Compute Bayes-optimal decision accuracy at every reachable partial history; check all conditional marginal-value inequalities. Compare myopic STOP-at-nonpositive-net-gain with the bounded two-observation policy. Run the candidate once, then a separately implemented raw-result auditor once, on native Ubuntu/WSL from the Linux filesystem. No model, GUI, input, network, or container.
- **D:** `PASS_METHOD_SCOPED` only if the exact enumerator finds the planted diminishing-returns violation, greedy stops at the empty history, the two-observation fallback uniquely has positive net gain under the frozen cost, and the independent auditor reconstructs all histories, marginals, policy decisions and scores while rejecting all mutations. This is a method-construction result only.
- **C:** A fixed depth-2 policy or simple checklist may be preferable; property-checking overhead may exceed any policy benefit; the result may depend entirely on the XOR construction.
- **U:** One authored four-world family cannot establish that real GUI evidence is adaptive-submodular, that the property is cheaply certifiable at scale, or that lookahead improves a live task. No probabilities are calibrated.

## Freeze

- Base main: `964c9197d5083ab55ea7fdc9105427623e89e677`
- Branch: `research/8879-assumption-gate-a01`
- Allocation: `8879-assumption-gate-a01-wsl-native-20261012-01`
- Candidate: `candidate.py`; independent auditor: `audit.py`
- The utility is decision accuracy improvement over the no-observation baseline minus a fixed cost of `1/100` per observation. The strict greedy policy stops when the best immediate net marginal value is not positive. The fallback observes both bits.
- First outcome is authoritative; no retry or parameter changes after execution.

## Scope / limits

The adaptive diminishing-returns condition is checked exactly on every compatible partial-history pair for this finite model. `PASS_METHOD_SCOPED` does not establish the condition for a general interface, nor an approximation guarantee for depth-2 lookahead. Result and audit bytes will be retained alongside this freeze.
