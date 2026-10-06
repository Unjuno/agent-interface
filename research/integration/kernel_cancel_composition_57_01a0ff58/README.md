# Kernel cancellation composition for #57

Read [REPORT.md](REPORT.md) and [PLAN.md](PLAN.md). This package records one
executed 96-row sequential source-contract matrix over eight subsets of three
existing repairs. It changes no promoted runtime and consumes no formal allocation.
All prospective source files, first child outputs, raw and original audit remain.

Read-only reconstruction, from this directory:

```sh
python -B -c "from pathlib import Path; import json; from raw_audit import audit; r=audit(json.loads(Path('run-01/raw.json').read_bytes())); print(r); raise SystemExit(bool(r))"
python -B -c "from receipt_audit import audit; r=audit(); print(r); raise SystemExit(bool(r))"
```

Verify SHA256SUMS.txt first. These commands do not rerun a producer or overwrite
any retained output. Programs whose command-line entry creates a named output
use exclusive creation and must run only in a separate copy with that output
omitted. The original prepare.py expects a sibling private `agent-interface`
Git clone; it is retained as provenance, not an in-place reproduction command.
The four modules in each sources/<RCU>/runtime/kernel are exact source subsets;
C+U is the conflict-free Git merge-file result. checks/ contains the all-three
production source plus the three authors' exact regression files.

Normal and optimized local composition regressions, in checks/:

```sh
python -B -m unittest runtime.kernel.test_kernel runtime.kernel.test_release_epoch runtime.kernel.test_cancel_release_epoch
python -O -B -m unittest runtime.kernel.test_kernel runtime.kernel.test_release_epoch runtime.kernel.test_cancel_release_epoch
```

No backend, physical input, container, GPU, model or live application is required.
Independent oracle implementation here is by this author; it is distinct from
non-author content review and full-repository/current-main merge confirmation.
