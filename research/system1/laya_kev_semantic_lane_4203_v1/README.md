# Laya vs Kev semantic-decision lane (#4203)

Status: intake/design reservation plus acquisition STOP only. No weights downloaded completely, no model loaded, and no formal inference row has run. The previously suggested 64-row threshold grid was not frozen or run; it is withdrawn as the formal T. Issue #4203's seven required strata and exact matched protocol govern.

## Scope and pins

Authority-neutral shadow comparison on the same local semantic-decision contract and identical rows. No OS task input, live GUI authority, execution, or remote inference. No fine-tuning in this discriminator. No general model ranking or model authority.

- Laya typed checkpoint `convaiinnovations/laya-typed-decisions`, revision `1a793eb568e6718f15941d08f85432581df534e3`.
- Kev adapter `jaredpalmer/kev-0.8b`, revision `9a45d25eb2ab761841196625383fa1dff0e56c1e`; base `Qwen/Qwen3.5-0.8B-Base`, revision `dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68`.
- Laya source `NandhaKishorM/laya`, revision `4066d5d5fbf08b66c6757ddeedbd797bd7655bc0`.
- Kev source `jaredpalmer/kev`, revision `5920c5fe4ca8e0970ed4209ac2c9b8e18bea5109`.

Never commit weights or tokens. Use separate dependency stacks as necessary. Network-disabled inference after exact artifacts have been staged and hashed.

## H — hypothesis

Under one frozen contract, either one candidate satisfies intent fidelity, YIELD behavior, and a declared local latency/resource envelope with no material value from retaining both; or the candidates occupy measurably distinct useful envelopes. Public model scores alone cannot discriminate this issue.

## T — matched comparison (not yet frozen or allocated)

The exact number and content of rows remain TBD; no evaluation may start until deterministic fixtures, independent oracle, serialized common inputs, adapters, and audit code are committed and hash-frozen.

The mandatory matched strata are:

1. `SAME_STATE_DIFFERENT_INTENT` — identical state with changed intent/constraints.
2. `SAME_INTENT_STATE_VARIATION` — held-out in-scope state changes.
3. `AMBIGUOUS_OR_MISSING_EVIDENCE` — expected YIELD.
4. `OUT_OF_SCOPE` — expected YIELD.
5. `OPTION_ORDER_PERTURBATION` — identical semantics, candidate order permuted.
6. `SHORT_STATE / LONG_STATE` — frozen context-length buckets.
7. `REPEATED_STATE` — measure reuse/cache separately from fresh-state.

Freeze a common input schema containing only `intent`, `constraints`, current typed state, last verified effect where applicable, bounded candidate descriptions, and scope/version metadata. Freeze model-specific serialization adapters before formal allocation; they may not add information unavailable to the other arm. Freeze candidate vocabulary (e.g. `CONTINUE`, `WATCH`, `REPAIR`, `YIELD`) with exact accepted disposition/effect rubric and forbidden proposal rules. Labels/oracle must be independent of both models.

## Measurements

Report separately: independently acceptable disposition/effect rate; same-state/different-intent; held-out state variation; required-YIELD recall; unnecessary-YIELD; forbidden/disallowed proposals; option-order sensitivity; fresh-state p50/p95/p99/max; repeated-state p50/p95/p99/max; cold load/warm startup; peak RSS/VRAM; artifact bytes; preprocessing/tokenization time separate from compute. Confidence/calibration is diagnostic only, never authority.

## D — permitted outcomes

Use only the scoped outcomes from #4203: `SELECT_LAYA_SEMANTIC_LANE_SCOPED`, `SELECT_KEV_08B_SEMANTIC_LANE_SCOPED`, `RETAIN_BOTH_DISTINCT_ENVELOPES_SCOPED`, candidate-specific semantic/YIELD `FAIL`, `HOLD_NO_DISCRIMINATING_TASK`, or `STOP_MODEL_OR_PROVENANCE_UNAVAILABLE`. Selection requires frozen criteria before results; no criteria are currently frozen, so no selection is permitted.

## C — competing explanations

Kev advantage might reflect broad language knowledge irrelevant to the bounded contract; Laya advantage might reflect narrow/task-distribution match; caching can dominate repeated-state latency but not fresh state; serialization may cause apparent differences; a deterministic rule/tree may suffice. Check each in interpretation; do not fold into a synthetic aggregate score.

## U — limits and safety

Hardware-specific results do not generalize. A failure of both does not justify escalating model size before representation sufficiency is checked. Outputs have no authority. Local Docker only; no GUI input, action execution, remote fallback, or fine-tuning in this discriminator. Define enforceable per-container memory/VRAM and wall-time ceilings before construction/formal phases.

## Phases

1. Freeze the issue-matched fixtures, input schema, independent oracle, adapters, primary endpoints/decision gates, corruption auditor, and exact expected artifact hashes.
2. Acquire pinned artifacts; verify every file; build separate local Docker images and construction-only load/dummy smoke. Record non-formal failures without changing inputs silently.
3. Freeze image digests, resource/time caps, fixtures/auditor/source/artifact hashes. Then run both models once over exactly the same preregistered rows, with Docker network disabled; measure fresh vs repeated-state paths separately.
4. Independently audit raw outputs and publish all primary measurements and scoped decision. Preserve STOP/FAIL/HOLD evidence unchanged.
5. Update this additive branch, CI-review via PR, and promote only the scoped candidate after evidence.

## Intake provenance

The previous Linux STOP was infrastructure/cache absence, not negative model evidence. On 2026-09-27 the user machine has RTX 3080 Laptop 16 GiB and responsive Docker Desktop 29.8.0 (Linux daemon 20 CPUs, 15.5 GiB RAM). HF metadata worked, but even the 3.58 MB pinned Laya tokenizer could not transfer: CLI timed out and direct curl stalled after 176,128 bytes. Exact evidence and resume criteria: `STOP_2026-09-27.md`. Independent clone failed, and existing dirty checkouts were left untouched; files were recorded via GitHub MCP to this additive branch.