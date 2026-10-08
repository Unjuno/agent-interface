# Issue #6471 T0 construction report

**Disposition: `HOLD_RESOURCE_WSLc_UNAVAILABLE`.** This records a frozen seven-case fixture and its construction checks, not the Issue's formal T0 decision or H-level hypothesis.

The T0 corpus covers equal-WER filler deletion versus recipient substitution, dropped negation, a Mae/May target substitution, a 4 MB/40 MB bound change, an explanatory quote promoted to an imperative, and an ambiguous recipient. H/T/D/C/U and the exact claim boundary are in [README.md](README.md). The independent raw-only auditor is separate from the candidate and has not been run.

On 2026-10-02, the first preformal construction test exited 1 after four assertions found capitalization mismatches in three source-span fixture literals; those were corrected. Independent review then found slot-label/source-span linkage was under-specified; after strengthening it, construction tests exposed an overstrict requirement for spans on null-valued optional slots. That was corrected, and the final `python3 -m unittest discover -s research/analysis/spoken_instruction_contract_preservation_6471_t0_20261002 -p 'test_t0.py' -v` exited 0 with 7/7 construction tests passing, including independent-oracle rejection of recipient, negation, speech-act and source-span mutations.

The formal candidate, formal auditor and retries are all **zero**. The task host is macOS/arm64; `wslc.exe`/`wslc` is unavailable. Because the governing cadence selects WSLc for this eligible local CPU experiment, no host or OrbStack substitution was made. No container was started or existing container touched. The construction PASS is not a scientific `PASS_METHOD_SCOPED`; the formal T0 remains HOLD.

Source SHA-256 identities, base commit, superseded unexecuted source revision and invocation counts are retained in [FREEZE.json](FREEZE.json). The method remains synthetic and structured: no audio, ASR, model, human, GUI, real effect, authority, safety or deployment inference.
