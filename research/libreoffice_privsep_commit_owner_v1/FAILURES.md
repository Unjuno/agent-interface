# Retained failures and incomplete allocations

These outcomes are retained separately and are not pooled with the successful pair.

1. **construction-01 — SETUP/HARNESS FAIL, unscored.** Parent `python-xlib` had no explicit private Xauthority and tried `/opt/xvfb/.Xauthority` before Calc discovery. No scored input/effect.
2. **c318-privsep-01 — HARNESS FAIL, 0 scored arms.** The UID proof incorrectly included the root `runuser` wrapper in the LibreOffice-process set and stopped before GUI task input. Frozen runner SHA-256 `b98d956850afa46909f0a7145cc5fe28f597215a14fedc97e239c304093bae56`.
3. **c318-privsep-02 — INCOMPLETE.** Stable arm completed. In the adversarial arm the UID-1001 writer attempted `os.replace` and got `EACCES`, but its result file ended with a literal backslash-n string, causing parent JSON `Extra data` before controller publication. Frozen runner SHA-256 `7de622b033aa86a742e418c2703d9a2bc30eee546b5cbf80f6a68df3df4c9d90`.
4. **c318-privsep-03 — completed successor.** Changed only the writer-result newline serialization relative to c318-02. Frozen runner SHA-256 `8e88d63e8d3db5bc02decde94b27b3a3e037eafba9917c09444d945557463a1c`.

No consumed allocation ID was retried or overwritten.
