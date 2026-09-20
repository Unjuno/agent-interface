# Hybrid Needle confirmatory pilot 04 — three seeds

Successor to [Issue #3458](https://github.com/Unjuno/agent-interface/issues/3458) pilot-03. The prior HOLD and boundary failure remain retained.

## H / T / D / C / U

- **H:** The fixed deterministic boundary margin plus learned interior proposal will meet the pilot-03 gates for all three fresh seeds.
- **T:** Frozen source SHA-256 `58437918FB96BE6D31D25C46E9B70A597BCBEC58C22835A953E5160AC1C46D13`; seeds 3461–3463; same balanced state generator, MLP, optimizer, steps, thresholds and 1,536-case boundary set as pilot-03.
- **D:** **PASS_HYBRID_MARGIN_SYNTHETIC_3_SEED_SCOPED**. All seeds clear per-class coverage >=75%, accepted accuracy >=.95, per-class recall >=.95, false CORRECT <=.5%, all boundary YIELD, state <=10 KiB, CPU p95 <60 ms.
- **C:** Only data/initialization seed varies; model and deterministic margins are unchanged.
- **U:** Three seeds, one hand-authored synthetic teacher. No Astra labels, pixels, live UI/servo, task effect, authority, or container execution. Seed 3462 only narrowly clears CORRECT coverage at 75.59%.

This modestly supports repeatability on the generated distribution, not transfer to real Needle tasks. See [runner.py](runner.py), [RESULT.json](RESULT.json), and Issue #3458.
