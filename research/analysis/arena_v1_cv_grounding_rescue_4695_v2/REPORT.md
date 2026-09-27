# Arena v1 CV grounding rescue v2 — local result

## Outcome: PASS_SCOPED_HELDOUT

This result follows the frozen protocol committed at `0c48312fc2a50d7d42d8f712cf0af62d1621192a`. Candidate, thresholds, inputs, and gates were not changed after freeze. The earlier v1 HOLD in PR #4743 remains immutable.

### Measurements

- Regressions: 12/12 v1 panels passed the corrected independent structure/output oracle, including all three multi-square ambiguity rows.
- Held-out: 4/4 unique-square positives localized with IoU 1.0; 8/8 absent, non-square, or ambiguous panels abstained. Each held-out ambiguous panel independently contained the expected 2, 3, 4, or 2 eligible components.
- Combined audit: 24 rows, 10 positives, 14 abstentions, zero errors. Lowest IoU was 0.9633058984910837 on the retained Arena panel; all other positive IoUs were 1.0.
- Retained out-of-bounds source point `[920,640]` remained attached to its proposal-only row.
- Mutation controls rejected 6/6: wrong positive box, proposal on absent, proposal on ambiguous, dropped denominator, duplicate identity, and altered input binding.
- Construction/oracle tests: 2/2 passed; generator replay was byte-identical for all 12 PNGs and the manifest.

### Reproduction

- Local pinned Docker helper: `sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261`, linux/amd64, Python 3.12/Pillow 10.2.0, CPU only, `--network none`, `--pull=never`; source and inputs read-only, output-only writable.
- Candidate source SHA-256: `d243d5febfbbc8ceccf5f707caa81435cfb3cb8a1200c6f38bbbc770c56e3da1`, byte-identical to v1.
- Held-out manifest SHA-256: `bf1410efd3f34963d95cfe6578a6fb272e760ec528b77083956c1965556b37ee`; held-out cohort is 41,594 bytes total including manifest. All 21 frozen files were read back from GitHub and matched local bytes before scoring.
- Raw rows: `predictions.json`, SHA-256 `627c8e6ddbdfd946408a743c47c9c7ddfc4361c10804ee681bebfa23ff8614d4`.
- Independent audit: `audit.json`, SHA-256 `376732593ec8495e919118fa7a0bdcd8f3c83e505e0b3478f1fe86113ed92eb0`.
- Mutation output: `corruption.json`.
- Commands: `python /src/test_audit.py /data`; `python /src/run_candidate.py /v1 /v2 /out/predictions.json`; `python /src/audit.py /v1 /v2 /out/predictions.json /out/audit.json`; `python /src/corruption_test.py /v1 /v2 /out/predictions.json`.
- No model/provider requests, GPU use, GUI, or input actions.

### Scope and integration boundary

This demonstrates only a deterministic orange-square proposal extractor on one retained frame plus fixed synthetic high-contrast scenes. It does not establish semantic grounding, general desktop robustness, real-app behavior, latency gains, or action safety. No click/runtime authority is created. Any reusable code/evidence still requires a PR and CI review before integration.
