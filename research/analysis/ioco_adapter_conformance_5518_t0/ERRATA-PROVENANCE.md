# Provenance erratum — Issue #5518 T0

This erratum supersedes the allocation-level PASS wording in the original result narrative without changing or deleting the retained `raw.json`, `audit.json`, or execution sidecar.

The local Docker candidate ran exactly once against the frozen source bytes in the workspace. Its raw record names source commit `798efe7ba45e22f393043878c5c600a1980afa4a`. Read-only inspection of that GitHub commit showed a concrete mismatch: committed `audit.py` is 6,609 bytes with SHA-256 `1a7059298b1fb51b1ea3c8eacb7e69e61c9d3465da9f02984ab9eaf726d2f44c`, while the frozen/executed file is 8,683 bytes with SHA-256 `613f70e52dc4c36334b7794e4e5a92849f20d06307ce5af109f2c32a5dee7ec2`. The MCP Git blob transfer stored truncated contents; the named commit therefore does not identify the source bytes that were executed. The raw file's source SHA-256 map matches the local frozen sources, but its commit pointer is false provenance. Independent recomputation of the finite fixture outcomes is still `PASS_T0_IOCO_SYNTHETIC_CONTRACT`; the allocation-level disposition is **`STOP_SOURCE_COMMIT_PROVENANCE`**, not a formal PASS.

No candidate rerun, seed substitution, raw edit, or audit edit was made. The full source and raw evidence are being republished over Git using ordinary Git object transport, with resulting blob and source-manifest verification. A later commit that contains identical bytes cannot retroactively repair the run's source-commit field. Preserve this STOP; any future formal allocation must use a new allocation ID and source SHA frozen before execution.

CI history (candidate never rerun):

1. `KeyError: image_pull_step` — workflow expected fields absent from the committed execution sidecar.
2. `SyntaxError: Non-UTF-8 code` — truncated Git blob caused auditor corruption.
3. `unexpected EOF` — nested shell quoting broke the audit-only job command.
4. A further audit-only workflow attempt failed before creating a job after the incomplete transfer. These are execution/evidence-delivery failures, not changed scientific outcomes.

The result is scoped to deterministic, hand-authored finite traces and does not test an actual adapter, GUI, task effect, runtime, or product safety.

## Hypothesis novelty correction

After execution, the full Issue #5518 comment history was rechecked. Existing T0–T7 already exercise input/output inclusion, hidden retry/batching, explicit UNKNOWN versus missing output, first forbidden prefixes, target/authority variants, nondeterministic output sets, exhaustive prefix checks, and bounded quiescence. The broad T0 hypothesis here substantially overlaps that completed sequence and is not a novel research result. This corpus adds stale-admission and false-semantic-success mutants, but no preregistered comparison established a distinct residual benefit over T0–T7. Preserve the fixture classifications as an execution record only; do not promote them as a new research PASS or close the Issue. The next experiment must target a clearly non-overlapping unresolved hypothesis or a formally specified successor question.
