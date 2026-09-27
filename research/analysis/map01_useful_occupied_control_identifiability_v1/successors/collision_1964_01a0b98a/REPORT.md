# #1964 — retained parallel-allocation collision (worker 01a0b98a-4d74)

Overall disposition: **STOP_COORDINATION_DUPLICATE_ALLOCATION**.
Computed finite-model outcome: `PASS_CENSORED_USEFUL_EFFECT_MEMBERSHIP_SCOPED`.
The computed outcome does not override the failed coordination gate.

## First retained outcome

Worker task: `01a0b98a-4d74-7552-9505-25cd77cc99e6`.
This worker created Issue #1964 and branch
`research/censored-useful-effect-successor-1838-20260919` from
`5432f3aa2374753e7ab206ad5e1f3f093ac0a641`. The exact seven-file source bundle was
published as commit `8f1488bf939eebb4eab8dc910f9e7b03dc3daabd` and all seven files
were read back through GitHub MCP before local formal execution.

The branch ref update failed with GitHub 422 `Update is not a fast forward`.
Subsequent readback found another source/result lineage:
`da25b0372fef64a37f9b13b1a5f3b4fa3ad6e23c` ->
`cee9e2874f94d2282916707f6847ba2eef70fb08`, PR #1971.
That PR also reported one formal invocation under #1964.

This worker's orchestration failed to stop on the rejected ref update and executed
the local formal, then its independent audit. Local counts are formal1/audit1,
reruns0/replacements0/tuning0. Issue-wide unique allocation is not established:
two distinct implementations/workers report execution. This is not pooled evidence
or a clean one-formal allocation. No attempt to repair the disposition by rerunning
is authorized by this retained identity.

The prior Issue comment's phrase "read-only-result audit" described intended audit
behavior, not a filesystem guarantee: the launcher mounts /out writable. Audit
source reads RAW/RESULT and writes AUDIT; it does not overwrite RAW/RESULT.

## Computed result and scientific limits

The frozen candidate and separately structured latent-world oracle agree on all
13,160 observations (658 edge domains x 20 cause/effect combinations).
Verdicts: TRUE 252, FALSE 11,340, UNKNOWN 1,568. Exact-edge UNKNOWN is zero.
39,200 inward-refinement comparisons do not reverse a known verdict. Seven invalid
input controls reject. Six independently audited tamper controls reject verdict,
missing row, duplicate row, endpoint, total and digest mutations; non-digest
corruptions have recomputed digests so rejection is not merely hash mismatch.

Counterexample: observed down [0,2], release [2,4], causal useful effect E=1.
World D=0,R=3 contains E in [D,R); world D=2,R=3 does not. Thus causal binding and
exact effect time alone do not identify physical membership under censored edges.
This changes the evidence model from #1838's known interval and explicitly uses
half-open occupancy. Parent #1838 is preserved, not reclassified.

No real clock comparability, physical truth, causal discovery, duration of useful
control, live model/GUI/gameplay, performance, recovery benefit or human parity
is established. Neither old v38/v39 evidence nor #1928 allocation is consumed.

## Reproduction and integration handoff

Source files are byte-identical copies of the published frozen bundle. Keep
SOURCE_FREEZE.json, RAW.json, RESULT.json, AUDIT.json and INVOCATION.json together.
Use run_container.sh with a new empty output directory for an explicitly labeled
external reproduction; do not relabel a new execution as the original formal.
The compact RAW format and corpus schedule are specified in PLAN.md.

Container: WSL Linux, Python 3.14.5, bubblewrap namespace isolation. Source and
/usr read-only; private proc/dev/tmp; output writable; no home, credentials,
desktop socket or external network mounted. Shared host kernel, no timing claim.
Initial environment-only probe failed because /lib64 mapping was missing; fixed
before source freeze and construction. Eight excluded toy construction checks
then passed. This setup probe did not execute the formal corpus.

This retention namespace is additive and worker-specific. Do not overwrite or
silently replace PR #1971. Its reported source/result hashes differ; that lineage
must be reviewed independently. Issue comments record the collision explicitly.

Next coordination requirement: treat any failed mutation result as a hard barrier;
recheck exact ref/source/ownership immediately before consuming an allocation.
An exclusive remote task claim needs verification; comments and branch existence
alone did not prevent this race. Further scientific work requires a fresh identity.
