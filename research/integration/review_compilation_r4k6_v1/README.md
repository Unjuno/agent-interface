# Retained CLI review fidelity — #4350

Existing behavior retained; new regression and evidence checks only.
See REPORT.md for first outcomes and limits; PLAN.md for the pre-execution gate.

```sh
python -S -B -m unittest -v runtime.cli_v1.test_review_compilation_r4k6
python -S -B research/integration/review_compilation_r4k6_v1/verify_publication.py
```

Run these from repository root. Never rerun consumed run_once.py for review.
180 review processes are not180 GUI trials. Exit0 means presentation completion,
not success of the historical task. No new input authority is granted.

The exact24 historical inputs and6 labelled derivatives are in input_parts.
Complete evaluation and construction outputs are in evaluation_parts and
construction_parts, described by RECORD_TRANSPORT.json. Sources are readable.
verify_publication.py is postmeasurement transport; frozen audit/controls remain
unchanged. Unrelated old blocked publications are not included.
