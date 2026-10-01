# LibreOffice macro interleaving boundary v1

## Result

`CONCURRENT_UNO_INTERLEAVES_MACRO_SCOPED`.

Ten frozen first cases completed on LibreOffice Draw 25.2.3.2.

- `window_stable`: 5/5 macro validated A=1000, the prerewrite observation remained 1000, and the macro wrote A=1200; B remained 5000.
- `window_concurrent`: 5/5 the independent UNO writer was connected before macro invocation, was released only after the macro validation barrier, completed `setPosition(1700)` after validation and before macro prerewrite, and the macro prerewrite observation was 1700. The macro then stale-wrote A=1200; B remained 5000.
- Independent audit passed all 10 cases with zero errors and verified the frozen ordering `macro validation < writer set start < writer set end < macro prerewrite < macro set < macro return` in every concurrent case.

## Interpretation

A single LibreOffice-hosted **Python macro invocation is not automatically an atomic document-mutation transaction against concurrent UNO calls**. The application accepted a second client's object mutation while the first macro invocation was still running. Therefore moving validation and mutation into one user-Python macro call is sufficient for stale-before-call rejection (#431) but not for compare-and-mutate atomicity under concurrent mutation.

This is a scoped negative result. The macro deliberately uses a fixed 500 ms `time.sleep`, which permits Python/UNO re-entrancy. It does not determine the semantics of a C++ extension, a SolarMutex-bound internal operation, a custom UNO service, or another application-owned transaction primitive.
