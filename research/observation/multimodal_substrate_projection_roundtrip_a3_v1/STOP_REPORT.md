# #1628 A3 preformal stop — exact source identity unavailable

## Disposition

**STOP_PREFORMAL_SOURCE_IDENTITY**. Formal invocations/results: **0/0**.

This preserves #1602, #1615 and #3207 unchanged. No source was reconstructed by approximation and no A2 scientific corpus was run.

## H / T / D / C / U

- **H:** individually published exact A2 source files could remove #1615's source-transport ambiguity without changing the A2 science.
- **T:** require the six SHA-256 identities frozen in #1628; recover exact bytes, publish each file individually, and require remote Git-blob plus SHA-256 readback equality before construction/formal.
- **D:** any source identity mismatch or inability to establish exact bytes is preformal STOP; only after all six identities match may the one permitted formal invocation run.
- **C:** the GitHub-retained A2 artifact is itself the historical mismatching bundle. A later #3207 120,000-row experiment uses a different allocation/protocol (including seed=0 and ten trace classes) and is not a substitute for the exact A2 source/seed/gates.
- **U:** the original local A2 exact files may exist outside GitHub, but they are not available in the GitHub evidence inspected here. Their absence from this search scope is not proof of permanent loss.

## Evidence checked

Current execution base at claim: `7e5ad7c0b50027fcec5414821b0685868c5212d2`.

#1628 requires:
- candidate.py SHA-256 `9b92239faa2d49c92632aef68ad8463890aadace672019704adeb145a9093f51`
- oracle.py `101df2d773c89261cda6d541a0362084dcb52ef55d874531746757e8bb1c520d`
- baseline.py `f2a74117cd14f57b002518372c91ce44179d9f77997001fc8255b740d1a706ed`
- formal.py `6fdcf1a89e64093ab71db41e65ce6c4e6a07c93ea103d247b5185baee505a575`
- audit.py `04fda01eea921cdca695b82410850db6c669730547594bce64431a2948eb6578`
- construction_a2.py `c13a3843c66222f2b8a59d45a8ebf6eda3aca1a8ddffd8ceb95e1addc5bc5cb1`.

Current main retains only A2 PLAN, CONSTRUCTION, SOURCE_MANIFEST, the historically mismatching `SOURCE_BUNDLE.tar.gz.b64`, and STOP_REPORT. PR #1626's five commits were read by exact ref: none contains the six source files individually.

The first local manual transcription of the remote bundle produced SHA-256 `728639a6fb474c002c293b4b58742afe2dad75aaf95fc96455f4f0f37f887a0f` and was rejected before decode/formal. Two connector-local experimental DEFLATE decoders also stopped during construction and produced no source files or scientific rows. These are tooling/construction failures, not scientific evidence.

## Stop rule

Do not recreate source from narrative, guessed code, #3207, or the corrupted A2 transfer. A future continuation may proceed only if the exact six source bytes become independently available and all frozen identities match before formal.