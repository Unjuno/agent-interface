# Issue #1940 successor — bounded attention budgeting

## H/T/D/C/U

- **H:** A typed attention budget can select the maximum-priority evidence package under a fixed cost while retaining raw evidence outside the selected hints.
- **T:** Enumerate every subset of six typed regions and every budget 0–17; compare the selected package to an exhaustive oracle with deterministic tie-breaking.
- **D:** `experiment.py`, 18 budget rows, raw-package SHA-256 values, exhaustive assertions, and this report.
- **C:** Every selection must be cost-feasible and oracle-optimal; raw evidence manifest remains present for every budget.
- **U:** Model usability, cue overload in real models, automatic region scoring, token/latency effect, GUI correctness, and transfer remain unknown.
- **STOP:** One finite standard-library run; no model, GUI, network, runtime, or user data.

## Result

Command: `python experiment.py`

- 18 budgets and all 64 region subsets were checked.
- Every selected package matched the exhaustive optimum.
- Maximum value at budget 17 was 19.
- Each row retained the complete raw typed region manifest and its SHA-256 digest.
- Result rows digest: `b94a43093472bbe8da157b484a0bf6970beff2d9d4d4249602967c664f968ec0`.

**Decision: PASS_ATTENTION_BUDGET_OPTIMALITY_SCOPED.**

This proves only finite allocation correctness. It makes no claim about model behavior, automatic scoring, token/latency reduction, GUI correctness, or runtime transfer.
