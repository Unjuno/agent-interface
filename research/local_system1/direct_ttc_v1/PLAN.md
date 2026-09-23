# LOCAL-SYSTEM1-DIRECT-TTC-20260917-001 source-first plan

Publication base: `6038e33c6034ad0b96c4d304f18874210a8c6925`; Issue #905.

One frozen mechanism: four sequential 16-float evidence chunks; six actions + internal CONTINUE_LOCAL + external YIELD. Direct TTC stage targets supervise CONTINUE before evidence arrival, action after arrival, and YIELD only after final local exhaustion. Stages1-3 may emit an executable action only at max softmax >=0.90; predicted YIELD/CONTINUE/low-confidence action continues locally. No task input or authority path exists.

Formal allocation: four seeds `[9051701..9051704]`; each trains one network on8192 rows for8 epochs, then evaluates fresh ordinary4096 + shifted/stress4096. Same trained weights are executed as FULL_DEPTH and DIRECT_TTC. Timing: ordinary cohort, batch1, one torch thread, 256 warmups +4096 measured calls/mode, counterordered by seed parity.

Decision gates are Issue #905 plus its two pre-source-freeze corrections: optimize paired mean/p50 latency rather than p95 because hard rows intentionally occupy >5% of the distribution; require ordinary premature executable output0 and stress <=0.10%; p95 may not regress >10%. No post-freeze threshold/signal/noise/width/epoch tuning.
