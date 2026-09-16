# Retained failures and incomplete allocations

These outcomes are retained separately and are not pooled with the successful pairs.

1. **construction-01 — SETUP/HARNESS FAIL, unscored.** Parent `python-xlib` had no explicit private Xauthority and tried `/opt/xvfb/.Xauthority` before Calc discovery. No scored input/effect.
2. **c318-privsep-01 — HARNESS FAIL, 0 scored arms.** The UID proof incorrectly included the root `runuser` wrapper in the LibreOffice-process set and stopped before GUI task input. Frozen runner SHA-256 `b98d956850afa46909f0a7145cc5fe28f597215a14fedc97e239c304093bae56`.
3. **c318-privsep-02 — INCOMPLETE.** Stable arm completed. In the adversarial arm the UID-1001 writer attempted `os.replace` and got `EACCES`, but its result file ended with a literal backslash-n string, causing parent JSON `Extra data` before controller publication. Frozen runner SHA-256 `7de622b033aa86a742e418c2703d9a2bc30eee546b5cbf80f6a68df3df4c9d90`.
4. **c318-privsep-03 — completed pathname-replace successor.** Changed only the writer-result newline serialization relative to c318-02. Frozen runner SHA-256 `8e88d63e8d3db5bc02decde94b27b3a3e037eafba9917c09444d945557463a1c`.
5. **c318-privsep-04 — HARNESS FAIL, 0 scored arms.** Direct-write source was invoked with a relative output path, producing a relative GUI HOME; Openbox could not create its cache and Calc never became ready. Frozen runner SHA-256 `c52f9e893442e99b59d7e3e259bab46e6f5702e2beaaf4412bc9ac1e4dd4bb0e`.
6. **c318-privsep-05 — INCOMPLETE.** Stable arm completed; direct-write arm fail-closed before the adversary because the real Calc fixture durable score was `A1=oldffice`, `A2=preview`. Frozen runner SHA-256 `c4d11da0d27960677856b1a5aa16dd3dec323c3ef0420b7c7efc17dad4512f75`.
7. **c318-privsep-06 — completed direct-write successor.** Changed only post-window setup settle from 0.6 s to 1.5 s plus fresh allocation/display identities. Executed runner SHA-256 `f7e54e9d9f4495ea8d13968cffe182accc84015573213bd77ae965b0b95c78fe`.
8. **publication integrity correction.** A manual full-source transcription of v6 produced a nonmatching Git blob and was deleted before being treated as authoritative evidence. GitHub now retains exact v3 source plus `runner_v6_direct.patch`; local reconstruction byte-matches the executed v6 SHA above.

No consumed allocation ID was retried or overwritten.
