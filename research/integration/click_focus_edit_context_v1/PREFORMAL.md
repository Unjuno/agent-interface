# Preformal source commitment

This commit is the public hash commitment before any formal #4148 case.

- allocation: `click-focus-edit-context-20260922-01`
- construction only so far; formal invocations: **0**
- final construction source/gates are bound by `FREEZE.json`
- local construction tests: 4/4 PASS
- construction failures 01/02: Xauthority setup STOP before input
- construction 03: original unfocused Entry bbox candidate was unusable and was replaced before freeze
- construction 04/05: corrected prefix-font-measure insertion coordinate construction passed; excluded from formal evidence
- formal command is fixed to three immutable batch slices of `SCHEDULE.json`; no case retry/replacement

Full readable source/raw bytes are published after the first formal outcome under this same additive namespace and must match every committed SHA.
