# Native measured-backend alias cleanup

One ordinary construction invocation on 2026-10-07 exercised the actual #8261 measured `Backend` constructor/validation/hold path, ExecutorV13 and V4/V12 owner on a private Xvfb. After the deliberately aliased `a`/`s` release batch failed, native cleanup neutralized the shared key before the failed terminal; a new `w` intent then completed. This supports this synthetic native composition only. It does not close #59 or authorize a live game.

**The frozen first audit remains FAIL 89/90.** The driver overwrote full-map fields in its final `mapping_setup` assignment, so audit v1 stopped at a missing field before reaching its program checks. Only two of its eight corruption controls added a failure beyond that baseline. A separate, post-run saved-data auditor v2 reconstructed the complete original/server map from the retained 248 `changed_rows` (every keycode 8–255) and passed **188/188** checks; its eight effective corrupted copies were all rejected. Neither candidate nor native input was rerun. The exact submitted map array and separate fresh full-array fields are absent from raw; reconstructing the submitted request depends on the pinned driver source. The original FAIL is not relabelled.

## Observations

| Boundary | Retained observation |
| --- | --- |
| Mapping | Stock a=38, s=39, w=25; fresh observer/session both resolve a=s=38, w=25 after changing only the private server |
| Alias admission | Two logical admissions; first DOWN confirmed with an actuation identity, second DOWN unconfirmed with no new identity |
| Failure | `ValueError('up_batch keys must resolve to distinct keycodes')`; zero completed steps; two incomplete `unknown_no_retry` UP rows, neither an ordinary release candidate |
| Cleanup | One native code-38 KeyPress/KeyRelease pair; one owner cleanup attempt observes down before and up after; no XTEST, sync or keymap error; verified neutral state precedes the failed terminal |
| Follow-on | New token after prior terminal, joined worker and inactive slot; w/code25 press/up with matched confirmed measurement identity; one completed step and neutral terminal |
| Observations | Eleven typed/full observation epochs, one reused synthetic PNG and eleven AIT artifacts; UNKNOWN HUD readers, no game/HUD accuracy claim |
| Teardown | Owner stopped, no watcher threads or remaining Xvfb process, unit inactive, owned VM stopped; 95 source hashes unchanged and 39 loaded images matched |

Source: `d9dc9dbfa09d89f10961e7cd7a8f52283b1c24c1`, with 95 selected images equal to the author-side virtual merge against main `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`. Debian12 arm64, Python3.11.2, Python-Xlib0.33, Pillow9.4.0, Xvfb21.1.7. The effective unit limits were 1 CPU, 1 GiB RAM, zero swap, 64 tasks and a 60s runtime cap. The actual namespace contained loopback and three unconfigured tunnel interfaces; the latter were down, unaddressed and unrouted. This prospectively declared gate does not amend #8094's historical `only_loopback` FAIL337/338.

## Difference from adjacent evidence

Pre-run overlap checks retained #8259 A10 at `2e0733e1ff2aea1665e90a4465fde004db44be30`. A10 has native owner/Executor evidence through its test-defined `Backend.execute`, which directly invokes owner calls and has a no-op validator. This construction exercises #8261's real measured backend and screenshot path, incomplete-release publication, and a fresh subsequent intent. It does not claim first discovery of native owner cleanup. #8250/#8259/#8094 raw, source and allocations are unchanged.

## Recovery and validation

`evidence.tar.xz` retains 407 inert members, 7,770,224 uncompressed bytes; archive 237,688 bytes, SHA256 `139329673d6d95cf2b9bc1edc126ec7bb499a6adc782031b4a12b12e44e2078f`. Every compressed member was read back and matched `MANIFEST.json`. Python files have a `.py.txt` suffix. All native raw, source, first audit, corrupted copies and their audits are byte-exact; only the two mutation invocation summaries replace private host paths with explicit placeholders. Their original hashes are in the manifest and original files remain private.

Extract the archive into a new empty directory. With Python and Pillow available, the following audits saved data only:

```sh
python audit_alias_v2.py.txt run-01/raw.json source-lock.json audit-repeat.json
```

Raw SHA256: `6b74aa9e466f8cbddf2569cafd292fd3ca7f881163e3f05e4ab2f90fb9d3df9a`.

The separately retained `native_alias_probe_v2.py.txt` fixes the fixture's final assignment to preserve incremental mapping fields. It passed syntax compilation only and was **not invoked**. The frozen driver is unchanged. The producer was authored by bugbot, the separate raw auditor by root, and the peer raw check is coauthor technical work; none is a nonauthor quorum vote.

No V39 controller, production Session launcher/stdin child, model, game, threat exposure, physical keyboard, application consumption, useful feedback, task completion, broad recovery or performance benefit is established. Main merge and the r139 live gate remain separate and unfulfilled.
