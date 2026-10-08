# Stratified Needle distillation pilot 02

Successor to the retained class-coverage HOLD in [Issue #3458](https://github.com/Unjuno/agent-interface/issues/3458).

## H / T / D / C / U

- **H:** Balanced training/testing would show whether the 435-parameter student preserves all three labels and exact transition neighborhoods, not just the majority class.
- **T:** Frozen runner SHA-256 `EF3C02E619FDBF25EDE311D799A4D1C326C1329C151015F10B692210B7FA2A99`; seed 3459; 2,048 train and 1,024 held-out cases per class plus 1,536 designed boundary probes; same student and 700 AdamW steps as pilot-01.
- **D:** **FAIL_BOUNDARY_FIDELITY**: balanced recall CONTINUE 1.000, CORRECT .9639, WATCH 1.000; false CORRECT 0; but boundary agreement only 768/1,536=.500 (<.90 gate). CPU p95 .038 ms; state 4,040 bytes. All five invalid gates YIELD.
- **C:** Same oracle, architecture, optimizer, and independent authority gate; this successor changes allocation design to balanced labels and explicit threshold-neighborhood probes.
- **U:** Synthetic teacher, one seed, designed boundaries; no Astra labels, pixels, GUI, actual servo/action or container run. High interior recall does not justify replacing exact boundary logic.

Disposition: prefer a hybrid candidate for a new preregistered successor—deterministic guard and exact threshold checks, learned proposals only within a validated interior margin, with YIELD on near-boundary ambiguity. Do not retrofit this conclusion into either prior result.

See [runner.py](runner.py) and [RESULT.json](RESULT.json).