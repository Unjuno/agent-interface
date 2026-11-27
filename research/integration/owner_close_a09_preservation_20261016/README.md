# #8874 A09 historical evidence preservation

Parent question: [#59](https://github.com/Unjuno/agent-interface/issues/59).
Original PR: [#8874](https://github.com/Unjuno/agent-interface/pull/8874),
head `6d008b53e23fda4703c8f56c4ea1bd762e5d147b`.
Integration base: `4c63725565f4dea433c49213b8d068c4c762f9bf`.

All **29 published files** are preserved byte-for-byte at their
[original path](../../doom/v39_owner_close_currentmain_a09_20261012/README.md).
[Original blob index](original-blobs.json) binds paths, Git blobs, lengths and SHA-256.
The historical `currentmain` name denotes the freeze's October 12 source,
`f185a9059d485a4f8d5a65e9e7f6782897f67eae`, rather than current qualification.
No candidate, native owner module, WSLc, Docker, X server, game or model ran.
This imports evidence only; no production behavior changes.

## Decisions

- **Preserve:** all publicly committed bytes, including source, first result,
  raw and the original manifest. No historical result is rewritten.
- **Incomplete original package:** the original manifest has 29 entries but
  `RUNNER/BUILD.log` is absent from the published head. Its expected SHA-256 is
  `4ac3aec06c7d5b75d9a143c4c6cd112a16faeb537ee15247486f392c98347b07`.
  The other 28 entries match; the manifest itself is the 29th preserved file.
  This check establishes absence from that head, not from every possible local store.
  The original PR's inline review had also identified this missing ignored log;
  this preservation does not dismiss or mark that finding repaired.
- **Scoped historical consistency:** the saved pure auditor's ten raw/source
  checks return its original `PASS_METHOD_SCOPED`. That does not make the
  package complete, qualify current source, or establish a physical release
  bound, task effect, actual session death, game progress or efficiency.
- **Continuation:** #59 carries the remaining control/recovery question.
  The source PR can converge to this preservation record without being described
  as directly merged or scientifically completed. Preserve its source branch
  until unique local evidence and ownership have been checked separately.

## Readback

`read_saved.py` checks original bytes and the manifest, requires the known
missing log to remain explicit, and invokes only the inspected pure saved
auditor. It rejects six mutations: keymap down, missing client events, missing
owner record, live owner thread, altered raw bytes and a missing original file.
Normal and optimized results are retained in `readback-normal.json` and
`readback-optimized.json`. The checks use explicit exceptions in both modes.

An initial reader used `assert` for some checks and failed its own optimized
tamper negative. Its source is preserved as `exploratory/reader-assert-red.py.txt`;
the corrected reader and both final outputs supersede that failed construction.
This is local saved-evidence verification, not a rerun of A09.

From the repository root:

```text
python research/integration/owner_close_a09_preservation_20261016/read_saved.py <fresh-output.json>
python -O research/integration/owner_close_a09_preservation_20261016/read_saved.py <another-fresh-output.json>
```

`SHA256SUMS.txt` inventories this new wrapper only. It does not replace or
repair the incomplete historical manifest.
