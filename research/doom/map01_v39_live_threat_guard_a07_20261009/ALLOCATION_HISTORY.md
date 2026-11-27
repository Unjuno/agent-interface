# A03–A07 allocation history

Every allocation is separate, one-shot, and preserved under its own local output directory. Setup failures were not retried in place.

| Allocation | Disposition | Evidence | Issue record |
| --- | --- | --- | --- |
| A03 | STOP before controller/game startup | ViZDoom and Xvfb passed; Pillow import missing; zero app-server requests. | [#6067039986](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-6067039986) |
| A04 | STOP during session startup | Guest session exited before `ready`; zero model turns/observations/input actions; game initialization unknown. | [#6067102920](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-6067102920) |
| A05 | STOP during V15 import | Missing `python-xlib`; zero model turns and control actions. | [#6067127807](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-6067127807) |
| A06 | STOP during V15 import | Missing `openpyxl`; zero model turns and control actions. | [#6067153285](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-6067153285) |
| A07 | HOLD after the full live episode | Ten planner turns; alive and unfinished; release custody passed after accounting for covers cancelled before any input. No hard-health guard or useful scorer event. | [#6067237106](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-6067237106). |

All A03–A07 raw allocation directories contain a per-file SHA-256 manifest. A07's original audit and additive v2 reconciliation are both retained; the correction does not overwrite the original audit output.
