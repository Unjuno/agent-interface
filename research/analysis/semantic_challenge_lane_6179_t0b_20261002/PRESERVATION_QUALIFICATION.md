# T0b pre-formal STOP: preservation qualification

Disposition remains **STOP_BEFORE_FORMAL**. Formal candidate and independent auditor invocations are both zero; there are no formal raw or audit outputs. The source base advanced before the formal start gate, so this allocation stays consumed and is not retried. The preceding #6179 `HOLD_METHOD_GATE_NOT_EXERCISED` is unchanged.

## Later clarification, without rewriting the original record

The unchanged [STOP record](STOP_BEFORE_FORMAL.md) describes the information available at the stop. In a [later owner verification comment](https://github.com/Unjuno/agent-interface/pull/6475#issuecomment-5944900375), a separate pinned-image WSLc diagnostic reported `/sys/fs/cgroup/memory.max=1073741824` under the same requested memory setting. The owner clarified that the warning concerns absent swap-limit capability, not absence of the observed 1 GiB memory ceiling. This was a separate diagnostic, not a rerun or a formal result for T0b. The main-advance STOP remains decisive; the owner assigned any later candidate/auditor activity to the distinct #6477 successor.

The original [execution comment](https://github.com/Unjuno/agent-interface/pull/6475#issuecomment-5944847708) and retained STOP report summarize one historical construction invocation with six passing tests. Complete construction stdout/stderr, a source-freeze hash manifest and the separate diagnostic's raw output are not among this seven-file package. Those historical statements are retained reports, not newly executed or independently reconstructed evidence.

## Custody and scope

All seven original package files from head `0925fe7e82cbe33e9f46f70a197bd1c8d01e0543` remain byte-for-byte unchanged. Their Git identities were checked against the exact committed bytes, and the three Python files were parsed without execution. That establishes committed-file custody, not the identity of bytes mounted in the historical container. The original README's pre-run wording and RUN_PROTOCOL's prospective instructions remain historical context; this qualification records the terminal interpretation.

No candidate, auditor, construction test, container, model, GPU, GUI or repository program was run for this preservation. No hypothesis PASS/FAIL, runtime benefit, production isolation, real verifier reliability or safety result is established. A later successor does not retroactively repair this STOP.
