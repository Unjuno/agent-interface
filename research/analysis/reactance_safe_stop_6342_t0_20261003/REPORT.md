# Issue #6342 T0 result

**Overall disposition: `HOLD_INDEPENDENT_REVIEW_REQUIRED`.** This is an executed method-only card-contract experiment, not a human-response experiment.

## Result

The frozen renderer ran once in an isolated OrbStack container and exited 0, emitting eight cards (four synthetic cases × two framing arms) and two planted negative controls. A separate, read-only-input auditor ran once and exited 0. It checked all four pairs and eight cards with zero structural errors; it rejected both the forbidden-retry mutation and the unsupported-success mutation. The verified-success control was present. The auditor therefore reports `PASS_STRUCTURAL_CONTRACT_ONLY`.

The preregistered full T0 gate also requires a separate blinded semantic reviewer. No independent reviewer participated in this run, so the allocation is held rather than promoted to `PASS_METHOD_SCOPED`. No card was rewritten and no candidate/auditor was rerun. The missing review is a genuine remaining gate for this T0 package.

## H / T / D / C / U

- **H:** Matched directive and autonomy-supportive cards preserve the same safety/evidence contract and an independent checker rejects deliberately unsafe/false-success controls.
- **T:** Four synthetic cases × two framings; two negative controls; six construction tests; one candidate and one independent audit, zero retries, OrbStack only.
- **D:** Structural contract: PASS; negative controls: 2/2 rejected; full method gate: HOLD pending independent blinded semantic review.
- **C:** Structural field and equal word-count checks do not establish equivalent comprehension, perceived autonomy, or reading time.
- **U:** No participant behavior, reactance, comprehension, safe-choice behavior, actual safety, GUI, audio, model, latency, or product result.

## Execution evidence

Exact commands: `execution/COMMANDS.md`. Frozen source/input identity: `FREEZE.json`. Counts, container IDs, exits, cgroup observations, host swap note and output hashes: `execution/RUN_RECORD.json`. Raw attached streams and exact extracted JSON are retained in `execution/` and listed in `SHA256SUMS`.

OrbStack was on `linux/arm64`, local Python image `sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b`. Candidate and auditor each observed cgroup v2 `memory.max=268435456`, `memory.swap.max=268435456`, `cpu.max=100000 100000`, and `pids.max=64`. These are process cgroup observations only. The Mac reported 8,111.25 MiB of 9,216 MiB swap already in use; no memory pressure was induced and the unrelated `unjuno-native-ci-6092` container was not touched.

## Interpretation boundary

This run can establish only that the authored safe-stop card fixture is structurally matched and that the independent checker rejects these two planted corruptions. It cannot establish the wording is perceived equivalently, that users understand it, or that autonomy-supportive language changes reactance or behavior. Issue #6342 remains open; any T1 would require its separately stated participant/privacy/accessibility and independent effect-truth gates.
