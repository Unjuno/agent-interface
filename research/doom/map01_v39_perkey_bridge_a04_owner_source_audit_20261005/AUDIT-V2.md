# Owner-source exact-type audit v2

The v1 owner-source auditor uses normal Python dictionary equality when
checking projected records. The v2 successor adds recursive JSON exact-type
comparison, so values such as `false` and `0` cannot alias inside nested
projected brackets.

The v2 test mutates only the projected bracket while preserving the original
owner source and recomputes the raw digest; the frozen v1 audit accepts that
mutated projection, while v2 rejects it. A separate adapter-edge boolean test
was dropped because the v1 gate already rejects that particular mutation using
`is False`; it is not evidence of the ordinary-equality gap. Both normal and
optimized v2 tests pass, and the unchanged retained raw passes the v2 audit.

The v2 audit/test source is an additive successor and is intentionally outside
the A04 freeze. `FREEZE-AUDIT-V2.json` binds the audit and regression-test
sources to the byte-identical retained candidate freeze/raw/result. The result
is stored in `AUDIT-V2.json`; historical A04 files remain unchanged.

Run `python3 -m unittest -v test_a04_v2.py`,
`python3 -O -m unittest -v test_a04_v2.py`, then `python3 audit_a04_v2.py`.
