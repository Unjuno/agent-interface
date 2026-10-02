# Allocation 06 — result

**PASS_RELEASE_INVENTORY_AUDIT_CONSTRUCTION_SYNTHETIC_ONLY (exact frozen-source rerun).**

Before execution, every preregistered file hash in FREEZE.json matched its frozen GitHub content. The byte-identical run in RUN_BYTE_IDENTICAL.json used CPython 3.14.5 (-B). The pinned 14-test fake-Xlib suite passed 14/14. The expected-inventory auditor accepted pristine and rejected empty trace, all brackets omitted, one bracket deleted, one admission deleted, terminal deleted, keycode corruption, and inverted timestamps. The predecessor raw-row auditor false-accepted the omission controls. v10 and v11 emitted the same six key requests, each used seven XSync calls, both ended with no fake keys down, and all three terminal records were verified neutral. A separate-process raw-only audit returned errors=[].

The earlier line-ending-normalized run remains preserved as RUN.json; it is not used for this PASS.

**Scope limits:** deterministic fake-Xlib on host only. No Docker/shared allocation, real X server, GUI, physical key-up, game, model, GPU, held-input occupancy, or MAP01 efficacy was tested. Formal X11 allocation remains unperformed; Issue #5156 remains open.
