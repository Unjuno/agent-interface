# Feasibility-aware estimability certificates — #7379 T0

## Question and scope

This finite CPU method test asks whether an auditable certificate can classify a named coefficient contrast over every observed support subset of a version-pinned set of feasible binary mechanism configurations. Each configuration is a three-bit tuple; factors are coded -1/+1. It compares a model containing an intercept, three main effects, and all three pair interactions with the saturated model that also includes the three-way interaction.

The method emits `ESTIMABLE`, `NOT_ESTIMABLE` with an exact null-space witness, or `UNRESOLVED_MODEL` when the two declared models disagree. It also reports a model-conditional minimum-cardinality feasible augmentation for non-estimable contrasts. These suggestions are diagnostics only and do not authorize any live experiment.

## H / T / D / C / U

**H:** For the finite configuration universe and feasibility predicates in `spec.json`, the candidate will classify every target contrast for every possible observed support subset, give valid exact witnesses, and find a lexicographically tie-broken minimum safe augmentation when one exists. It will never recommend an infeasible arm.

**T:** Enumerate all support subsets for the four declared feasibility sets (464 supports total), three target contrasts, and both model profiles (1,392 contrast/profile results). The candidate uses rational row reduction. The independent auditor uses fraction-free exact minor determinants for rank, checks row-space/null-space witnesses by exact arithmetic, recomputes repair minimality, and runs five corruption controls. Candidate and auditor are each invoked once after the freeze.

**D:** `PASS_METHOD_SCOPED` requires exact agreement across all 1,392 results; valid witnesses; complete unique support enumeration; no unsafe or nonminimal repair; positive, alias/no-repair, one-arm repair, and hierarchy-sensitive cases; and rejection of all five mutations. Any false certificate, unsafe repair, or missed cheaper safe repair is `FAIL_METHOD`. A conclusion that changes with the declared hierarchy remains `UNRESOLVED_MODEL`, not an unconditional estimability claim.

**C:** An accepted effect hierarchy may make the compact model sufficient; the saturated model can require more support. Real mechanism configurations may also vary by version, carry over between tasks, interact at unmodeled orders, or violate the declared feasibility predicate.

**U:** This establishes finite arithmetic and audit behavior only. It does not identify causal effects, prove randomization or consistency, assess power/variance, validate a feasibility policy, or authorize any model/GUI allocation. Outcome data are not generated or imputed.

## Reproduction

From this directory, using Python 3.14.5 standard library:

```sh
python3 candidate.py spec.json output/raw.json freeze.json
python3 audit.py spec.json output/raw.json freeze.json
```

Each formal command is frozen for one invocation. The first candidate and audit outputs are retained in `output/`; do not overwrite or rerun them. Exact source, spec, main and command identities are in `freeze.json` and `PRELAUNCH_FREEZE.md`.
