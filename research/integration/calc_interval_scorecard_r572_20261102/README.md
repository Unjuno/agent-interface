# Calc task and launcher interval scorecard

This is a post-hoc descriptive re-audit, not a new live experiment. On main `af5cf091b952907590cd56a76e8c7d24c4ea5fb5`, the existing `compare.py` re-audited both retained WSLc LibreOffice blocks ([fixed order](../wslc_calc_three_arm_obstruction_20261101/) and [reverse order](../wslc_calc_three_arm_obstruction_reverse_20261101/)); it exited 0 without Python optimization. Its output is `comparison-audit.json`; `scorecard.py` computes the following medians from those six audited attempts.

| Route | Task interval median | Launcher interval median | Input tokens median |
| --- | ---: | ---: | ---: |
| Direct | 9.278 s | 12.961 s | 25,751 |
| Compiled | 10.150 s | 12.476 s | 25,751 |
| Fresh | 12.096 s | 15.813 s | 40,666 |

Compiled minus direct is +0.872 s for the task interval and -0.485 s for the launcher interval. With two observations per route and fixed/reversed block order, this is a scope sensitivity observation, not a causal speedup or reliability estimate. The launcher interval includes launching the model host and container, but excludes preparation and audit; it is not full lifecycle cost. Fresh intentionally uses one more model call. Both blocks use the same fixed 472/615 LibreOffice task, test-controlled temporary obstruction, expected-value OCR and scripted Save. No new provider call, GUI execution, or allocation was made in this re-audit; original results and limits are unchanged. Raw model protocol journals remain omitted as described by the source blocks.

Run `python scorecard.py` in this directory to recompute the added medians. To rerun the underlying independent verification, extract both original archives and run the reverse block's `compare.py` without `-O` and with Pillow, as documented there. Exact JSON may contain more precision than the rounded table.
