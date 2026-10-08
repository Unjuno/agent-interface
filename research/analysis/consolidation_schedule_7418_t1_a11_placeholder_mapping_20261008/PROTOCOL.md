# Issue #8406 T1 A11 — symbolic slot mapping

## Rationale and delta

A10 completed all 390 calls but the independent auditor returned `FAIL_METHOD` with 54 transition violations: wrong exception claim kind, literal field-name used as fact key, omitted version in history key, source-ID errors, wrong exception effect, and conflict mismatch. The descriptive answer-arm contrasts are not interpreted because the transition gate failed. A11 is a new allocation with fresh seeds. It keeps the exact T0 episode corpus and query set, schedules, model digest/family, decoding, call count, and auditor. The only intended change from A10 is clearer symbolic, placeholder-only output mappings. No A10 output is reused.

**H.** Explicitly showing each generic input-to-output mapping with typed symbolic slots, and stating that slot labels are not literal values, improves faithful transition output on this fixed synthetic corpus.

**T.** Four frozen schedules; six prefixes; five fixed queries; seeds 5101, 5102, 5103; 360 query calls plus 30 consolidation calls, 390 total. Qwen3:8B at the frozen digest, Ollama 0.40, private loopback service/store, JSON output, `think=false`, temperature 0.2, top-p 0.9, context 8192, query cap 128, consolidation cap 2048. No warmup, retries, or action authority.

**D.** The only cadence decision follows the inherited preregistered rule: >=0.10 consistent contrast across all seeds plus clean transition/raw audit is scoped sensitivity PASS; all contrasts within margin plus clean gates is scoped no-material PASS; any transition/method error is FAIL_METHOD; otherwise UNCERTAIN. No production policy inference.

**C/U.** Prompt comprehension, model stochasticity, fixture/query selection, and the single model family remain limitations. Any clean result is limited to this synthetic corpus and model configuration.

## One-shot execution

Run the construction tests before freeze. After freezing the full source/input/auditor/model contract, run the candidate once to a new exclusive raw path and the auditor once only after all 390 calls complete. Preserve every output. No retry, prompt edit, or reuse of this consumed allocation.
