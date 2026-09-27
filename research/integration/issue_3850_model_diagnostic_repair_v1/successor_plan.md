# Successor allocation — Issue #3850 matched-model repairability

Parent allocation: `ALLOCATION_01_STOP.md`, formally unconsumed (0 model calls), preserved unchanged. This is a separately frozen successor, not a retry or continuation of any row.

## H/T/D/C/U

**H.** On two previously observed malformed `observe` program shapes, a bounded static refusal detail enables more exact same-model program repairs than the generic `INVALID_PROGRAM` code alone.

**T.** Eight fresh, one-turn `gpt-5.6-luna` low calls via host CLI 0.158.0-alpha.2. Two cases × two repetitions × two arms, with the fixed order in `cases.json`. Sole pairwise difference is the refusal payload. Use the explicit corrected one-Task prompt in `successor_prompt.txt`; do not read schema/docs into the model prompt. Output schema and exact-repair oracle remain those in the frozen cases and response schema.

**D.** Count READY only if its full program equals the independently authored expected JSON object, preserving every unrelated field, ROI, frame and release_all. YIELD is safe abstention, not repair. PASS only if BOUNDED_DETAIL has more exact repairs than CODE_ONLY and zero false READY. Fewer detailed exact repairs or any false detail-arm READY is FAIL_DETAIL_HARM; tie/mixed/no repair is HOLD. Any row/process/provenance/audit gap is STOP/HOLD, never model failure. Four pairs are underpowered and descriptive only.

**C.** Same model, CLI build/hash, host, program, ROI, prompt except refusal JSON, schema, one-turn budget and order; fresh conversation per row. Local Docker Desktop linux/amd64 pinned image, network none, read-only root, one CPU, 2 GiB, 64 PIDs, dropped caps and no-new-privileges. Host broker only forwards one request per Docker row to the host Codex CLI. No workflow, GUI, image, dispatch, input, tools, retries or substitutions.

**U.** Two authored cases and four pairs only. No natural error rate, user recovery, avoided-call count, latency/cost claim, task success, cross-model transfer or execution-safety conclusion.

## Execution boundary and corrections

- Formal execution is allowed only after two independent Docker snapshots at least 30 seconds apart show no unknown active containers and no CPU-consuming jobs; any newly appearing unknown container resets the quiet-window timer. Known long-lived idle Ollama remains present at the baseline state; it is not stopped or inspected internally. If this gate cannot be satisfied, STOP without calls.
- Check this gate immediately before each row. One request ID/CLI invocation per row, no retry. Preserve each first outcome and stop subsequent allocation at any transport/provenance failure.
- Resource availability in Docker Desktop was observed as approximately 15.5 GiB total in the active unrelated-container snapshot. Runner stays capped at 1 CPU/2 GiB. If unknown workloads appear, do not run concurrently.
- The parent allocation's failure was detected before any prompt reached the host CLI. This successor eliminates the duplicated task sentence by using an explicit literal prompt with exactly one `Task:` and keeps the exact same conditions/decision gates.
- Keep the current-main source evidence pinned to the original intake blobs and recheck main at allocation start. No runtime code modification.
- Retain source/gate hashes, local Docker construction and negative controls, exact prompts, request/response IDs, raw JSONL, CLI argv/version, token usage, process receipts, images/runtime IDs and an independent network-none raw-only audit. Record all outcomes in Issue #3850; publish only additive evidence through a reviewable PR after successful audit and local checks.

## Invariants

Formal calls = 0 until all preregistration files are read back from GitHub and all local hashes/gates match. No GitHub Actions/workflows execute any trial.
