# Retained result — Chromium procedure guarded macro v1

Decision: **PASS_CHROMIUM_GUARDED_MACRO_COMPILATION_SCOPED**.

The byte-frozen task1 frontier procedure compiles into a typed macro with parameters `token`, `field_handle`, and `submit_handle`; the artifact contains no executable absolute field/submit coordinates and no fixed task1 token. It is compiled once.

Formal replay: 6 retained states x 2 artifacts = 12 rows, exactly one invocation, reruns0.

- task2/task3 layout-A: literal replay and guarded macro both match the retained current A target.
- task4 pre-repair: the retained window focus/surface/geometry is unchanged, so literal replay remains apparently applicable and emits historical task1 A coordinates. The guarded macro sees old field handle status `missing` and yields before any pointer event.
- task4 post-repair/task5/task6 layout-B: the same compiled macro accepts current B handles and matches the retained current target without recompilation. Literal replay still emits the A points and mismatches B.
- independent audit errors `[]`; four copied-result corruptions reject4/4; all frozen source hashes and fixture hash remain exact postformal.

Descriptive local decision timing is micro-scale (literal median below 0.001 ms; guarded median about 0.010 ms in this Python replay). This is **not** a GUI latency or productivity claim.

## Boundary

This is retained-evidence representation/composition evidence only. It does not rerun Chromium, establish new task success/token savings, infer arbitrary procedures, or show that every frontier-authored trace can be compiled. The compiler recognizes exactly the frozen field-entry method vocabulary and existing target-handle roles. Its value is the scoped boundary: procedure semantics can be retained while absolute target identity remains a runtime parameter guarded by current evidence.
