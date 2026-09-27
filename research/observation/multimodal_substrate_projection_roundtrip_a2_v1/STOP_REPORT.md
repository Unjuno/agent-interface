# #1615 preformal source-integrity stop

Decision: **STOP_PREFORMAL_SOURCE_FREEZE_MISMATCH**.
Scientific disposition: **NONE**. Formal invocations/results **0/0**; reruns/replacements/tuning0.

The A2 accounting construction passed locally, but mandatory remote readback found that the GitHub-retained `SOURCE_BUNDLE.tar.gz.b64` does not match the frozen manifest:

- manifest/local intended bundle text SHA-256: `23e5e7014444da8aea7129a54bf5851ffdf369d4cd5326fe9033a75ec207019e`
- remote GitHub blob SHA: `14bc0c612c6fc37606c35d0999804656fd888399`
- remote blob content length: 8376 bytes
- independently computed remote text SHA-256: `728639a6fb474c002c293b4b58742afe2dad75aaf95fc96455f4f0f37f887a0f`

Because source identity is a preregistered gate, formal execution was not started. The branch is retained as-is; the mismatching freeze is not overwritten and no A2 result is inferred.

A fresh successor may preserve the exact A2 science/accounting repair while changing only source-retention packaging: publish the semantic sources as individually hash-checked text files, verify each remote Git blob against local exact bytes, then start formal only after all identities match.

No model/provider/GUI/X11/network/task input/shared-runtime activity occurred.
