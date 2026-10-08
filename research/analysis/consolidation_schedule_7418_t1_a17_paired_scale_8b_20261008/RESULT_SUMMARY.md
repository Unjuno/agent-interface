# T1-A17 paired-seed model-scale result

## Outcome

The frozen Qwen3 8B candidate completed all 390 planned calls across seeds 5601–5603 with zero candidate call errors. The independent transition auditor ran once and returned **`FAIL_METHOD` with 24 errors**. The preregistered interpretation therefore stops at failed transition fidelity; schedule contrasts below are descriptive and do not establish cadence sensitivity.

The same two failure families appeared in each seed:

- `ep03` rare-exception claims encoded `effect=draft_saved; forbidden=publish` instead of the ledger's `effect=no_external_effect; forbidden=publish`. This generated 12 unfaithful transition claims across `per_episode` prefixes 3–6 and `terminal` prefix 6.
- `batch_2` introduced `conflict:revision-r7-mode` at prefix 4 before the second conflicting observation was available; at prefix 6 the explicit conflict claim still mismatched. These generated 9 additional errors.

The remaining three errors are the repeated per-seed premature conflict and transition coverage checks grouped above; total auditor error count is 24 (8 per seed). See `results/FORMAL_T1_A17/audit.json` for the exact per-transition list.

## Seed-matched descriptive accuracy

Each seed had the same exact-answer score:

| Schedule | A17 Qwen3 8B | A16 Qwen3 14B | A17 minus A16 |
| --- | ---: | ---: | ---: |
| episodic_only | 0.267 | 0.800 | -0.533 |
| per_episode | 0.533 | 0.667 | -0.133 |
| batch_2 | 0.633 | 0.789 | -0.156 |
| terminal | 0.667 | 0.633 | +0.033 |

Within A17, `terminal` exceeded `episodic_only` by 0.400, `batch_2` exceeded `episodic_only` by 0.367, and `per_episode` exceeded `episodic_only` by 0.267 in every seed. These are unvalidated endpoint differences because the transition audit failed. A16 passed its audit and showed the opposite direction for episodic-only versus per-episode and terminal; the discrepancy motivates further diagnosis, not pooled or causal model-scale claims. Numeric seeds are matched, but random streams are not coupled across model sizes.

## Calls and costs

Every A17 seed-arm completed 30 query calls; consolidation calls were 0 (`episodic_only`), 6 (`per_episode`), 3 (`batch_2`), and 1 (`terminal`). Across the three seeds, total prompt/completion tokens and measured request duration were:

| Schedule | Calls | Prompt tokens | Completion tokens | Request duration (s) |
| --- | ---: | ---: | ---: | ---: |
| episodic_only | 90 | 31,293 | 2,006 | 102.7 |
| per_episode | 108 | 50,964 | 4,293 | 189.9 |
| batch_2 | 99 | 38,412 | 3,366 | 144.0 |
| terminal | 93 | 24,246 | 2,526 | 111.7 |

Duration is the sum of recorded request durations on this local run, not a controlled latency comparison. See `results/FORMAL_T1_A17/checkpoint_metrics.json` for checkpoint, query-family, token, and cost details. Its exact-answer reconstruction matches the independent audit's per-seed values; the metric artifact itself records `FAIL_METHOD`.

## Scope and integrity

This is one synthetic ledger, one local Qwen3 family, three fixed numeric seeds, and a failed method gate. It does not establish GUI/product effectiveness, action safety, or general model-scale effects. A17 was not pooled with A16. Candidate and auditor each ran once; no generation or audit retries occurred. The private Ollama server was stopped after preserving outputs.

- Model: `qwen3:8b`, Q4_K_M, digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
- Raw JSONL SHA-256: `be195abb542aa7553823490ae84049f187ab6f976f7e199a0bb3a51691d3414b`.
- Audit JSON SHA-256: `db63226b1755033726d2c3ceb276b44ed3ea860ef96a34d765dd367cfc348f6e`.
- Metrics JSON SHA-256: `6b4649352352b2551edec8150fef905b1759608a03392d5ff5825710edf449bf`.
- Frozen preflight SHA-256: `6da8bac784df465ba4d249a5b956e457ee0ad88a5c0065ec089dad2cbb4490db`.

The allocation was preregistered on [Issue #8406](https://github.com/Unjuno/agent-interface/issues/8406#issuecomment-6052360718). A16 comparator audit and metrics were read from commit `6fc59c871`; A16's own independent audit was `PASS_METHOD` with zero errors.
