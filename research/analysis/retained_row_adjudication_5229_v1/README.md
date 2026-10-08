# Retained-row adjudication for #5229

Read [REPORT.md](REPORT.md) for the conditional table and scientific HOLD.
[PLAN.md](PLAN.md) and [FREEZE.json](FREEZE.json) define the original analytical
scope. No historical runner is executed.

From a checkout with the frozen source commit available, run:

```sh
python -B -m unittest discover -s research/analysis/retained_row_adjudication_5229_v1 -p test_adjudication.py -v
python -B research/analysis/retained_row_adjudication_5229_v1/adjudicate.py > adjudication-review.json
python -B research/analysis/retained_row_adjudication_5229_v1/audit.py adjudication-review.json
```

Use `--git` with an explicit Git executable if necessary. Write review outputs
outside the retained evidence directory. These commands reproduce ordinary
analytical validation; they are not a new formal/kernel experiment. The
author's first outputs are in [evidence/](evidence/).
