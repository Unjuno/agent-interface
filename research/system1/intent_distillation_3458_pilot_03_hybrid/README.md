# Hybrid Needle distillation pilot 03

Issue [#3458](https://github.com/Unjuno/agent-interface/issues/3458), successor to pilot-01 class-coverage HOLD and pilot-02 boundary-fidelity FAIL.

## H / T / D / C / U

- **H:** A fixed deterministic validity/margin gate can reject uncertain threshold neighborhoods while a small learned head proposes decisions only in the interior.
- **T:** Frozen runner SHA-256 `50A9F68BB9B8D3C0878C0D5627B3DF182344CEB68ADE8451956067412D5DA5FA`; seed 3460; 2,048 training and 1,024 held-out cases per class; 1,536 paired boundary cases; same 435-parameter head and 700 AdamW steps as pilot-02.
- **D:** **PASS_HYBRID_MARGIN_SYNTHETIC_SCOPED**: 2,616/3,072 accepted (85.16%); accepted accuracy .9958; per-class coverage .771 or higher and recall .988 or higher; 7/2,616 false CORRECT (.268%); all 1,536 boundaries YIELD; all four stale/invalid probes YIELD; CPU p95 .0597 ms.
- **C:** Same synthetic teacher/head as pilot-02; changed mechanism is a pre-inference deterministic margin gate.
- **U:** One seed and hand-authored teacher; no Astra labels, pixels, live GUI, action, task effect, or container run. Does not establish robustness or product real-time.

The narrow result supports the hybrid candidate only on this synthetic distribution. Next: multi-seed transfer and externally authored intent annotations before any runtime integration.

See [runner.py](runner.py) and [RESULT.json](RESULT.json).