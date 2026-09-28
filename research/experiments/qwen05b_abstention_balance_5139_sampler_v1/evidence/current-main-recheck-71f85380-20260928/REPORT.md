# #5139 current-main construction compatibility recheck

## Disposition

`PASS_CURRENT_MAIN_CONSTRUCTION_COMPATIBILITY_ONLY`. The additive sampler package from PR #5165 applies cleanly to main `71f85380669795d21c668bcbc832ae896d0b6220`; after repairing a probe import-path defect, its host construction suite and both fixed 128-sentinel design probes pass. This is not a pinned-container, model, CUDA/GPU, LoRA, quality, safety, or formal-allocation result.

## H / T / D / C / U

- **H:** The #5139 additive sampler, independent auditors, and synthetic support-construction diagnostics remain executable and deterministic when composed with the frozen current-main snapshot above.
- **T:** In a newly created shallow/partial clone, fetch PR #5165 head `95755d5d9a125ff53e0fea2b51cf1c08d03264f0`; verify merge base `e74f0ba20f7b7476ab9b3e62f8533ec53d216daf`; merge the additive PR changes and main `71f85380669795d21c668bcbc832ae896d0b6220` into the isolated branch. After the first root-level launch exposed a missing import bootstrap, add an ancestor-based package path lookup and subprocess entrypoint tests with `PYTHONPATH` removed. Run the complete suite and both probes directly from repository root. Compare output JSON with prior retained `result.json`.
- **D:** Final Python 3.11.9 host suite: **27/27 passed** (0.943 s), including two repository-root probe-entrypoint regression tests. Both direct probe commands exit 0; marginal and joint-cell probes each pass **128/128** sentinels. Parsed output matches each retained result JSON; stderr is empty. The pre-fix suite was 25/25; one intermediate new test failed on its own incorrect count-key assumption and is disclosed below. Current-main merge was clean; before the final source-only fix, `origin/main...HEAD` reported 0 behind / 16 ahead (the branch includes the additive PR history and current main).
- **C:** One Windows host, CPython 3.11.9, deterministic synthetic fixtures/sentinels, exact main SHA and PR head recorded above. No new allocation seed, model/checkpoint load, CUDA call, GPU work, Docker/OrbStack invocation, fit, adapter write, or formal output.
- **U:** This confirms compatibility of the additive research bundle with that main snapshot; its protocol/generator are the package's frozen copied sources, not a new audit of all production dependencies. It does not resolve the support-arm row-identity/multiplicity limitations or establish model effects. The historical `sad_cannon` attribution remains unrecoverable; the terminal HOLD recorded in #5139 comment 5864223178 satisfies only the gate's uncertainty-retention clause, not a zero-fit or no-overlap proof. Pinned-image, fresh data/model/tokenizer freeze, collision, and exclusive GPU/Docker lease gates remain separate.

## Commands and retained output

```text
python -m unittest discover -s research/experiments/qwen05b_abstention_balance_5139_sampler_v1 -p 'test_*.py' -v
Ran 27 tests in 0.943s — OK

python research/experiments/qwen05b_abstention_balance_5139_sampler_v1/evidence/feature-marginals-128-20260928/feature_design_probe.py
python research/experiments/qwen05b_abstention_balance_5139_sampler_v1/evidence/joint-cell-marginals-128-20260928/joint_matched_feature_probe.py
```

Both direct commands exited 0 from repository root with no `PYTHONPATH` assistance. The captured post-fix output files and empty stderr files are in `evidence/probe-entrypoint-fix-20260928/`; parsed values match the earlier retained results.

| Artifact | SHA-256 |
|---|---|
| Feature-marginal probe source before import fix | `FA2F470E68AE561C43B561BE9D3606B99919F4F5969A630F2F5A44A3C92AFC9A` |
| Feature-marginal probe source after import fix | `17A46B3B5298192AD8E04C8DB8151029467AE47DC6CD201D26223E6E133ABDA8` |
| Entrypoint regression test source | `094CC12D90123342D9B828035F5290BF010167FAD7A7CA1BD82DCCAFB1DEDDE3` |
| Joint-cell probe source | `C119067BAF68681C2E90E344B4BD0012DBA93AFA17F16AF534262FF2F4EB7F87` |
| Marginal probe stdout | `42E3E0E353C824570C8BF71491F25AFA89F9DD30A0D48D5295EE3E79EE160A25` |
| Joint-cell probe stdout | `57D6BE4203C8AFA8CE272E433FB7710362A47E52EC049EBD35FD0737D157E3CF` |
| Each stderr (empty) | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` |

## Preserved invocation / hygiene failures

1. Before the import fix, running `python research/.../feature_design_probe.py` from repository root exited 1 before probe execution: `ModuleNotFoundError: No module named 'make_dataset'`. No output was produced. The fix adds only `__file__`-ancestor discovery for the package containing `make_dataset.py`, `protocol.py`, and `sampler.py`; deterministic selection logic is unchanged. The post-fix direct run exits 0 and matches the retained result JSON.
2. The first run of the new entrypoint test suite was **26/27**, with the new feature-probe test raising `KeyError: 'sentinels'`: the marginal result schema reports `sentinel_support_seeds`/`runs`, while the joint result uses `sentinels`. The test oracle was corrected to accept the declared keys; the final full suite then passed **27/27**.
3. `git diff --check origin/main...HEAD` reports an extra blank line at EOF in the copied `protocol.py` (line 157). That file preserves the frozen #5014 source bytes and is intentionally not edited here; this is a disclosed source-format warning.

## Resource gate

The latest read of #5085 still shows a live shared Docker client and an unobservable OrbStack inventory; #5139 has no named exclusive GPU/Docker lease. The `sad_cannon` attribution remains unrecoverable; #5139 comment 5864223178 records a terminal HOLD that satisfies only the uncertainty-retention clause, not zero-fit/no-overlap proof. This recheck therefore stayed on host CPU. No resource ownership or formal-run authority is inferred from an idle GPU or a successful CPU test.
