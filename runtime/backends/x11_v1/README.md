# X11 backend v1 integration candidate

This adapter binds the promoted `runtime/core_v1` semantic contract to X11/XTEST.
It is derived from the retained private X11 backend conformance result but is not
by itself a general Linux or WSLg support claim.

Current scope:

- explicit registered target windows;
- screen-physical and window-client coordinates;
- capture, keyboard, strict-ASCII text, pointer, scroll, focus, wait/feedback and verified release;
- core admission occurs before any XTEST emission;
- X11-specific whole-program preflight rejects unsupported native constraints before the first emission;
- native preflight failures return typed `BACKEND_CONSTRAINT` refusals;
- backend execution exceptions force a release attempt;
- integration tests use an independent Tk application effect file rather than backend-internal success inference.

Run in a private X11 session:

```bash
python -m unittest -v runtime.backends.x11_v1.test_integration
```

Promotion beyond this candidate still requires supported-host/application coverage.

## Preflight refusal evidence

A BACKEND_CONSTRAINT refusal before the execution loop explicitly records
`program_execution_started: false`, `program_emissions: 0`, and
`cleanup_attempted: true`. `backend_emissions` remains the cumulative connection
counter, including prior programs and any cleanup release events. These fields
therefore do not claim that no physical input occurred: inspect the separate
release/readback and recovery evidence. The public outcome summary preserves
these explicit fields without inferring them for historical receipts or other
backends. No replay is authorized by the summary.

This addresses the ambiguity encountered in the retained
[primary Calc trial](../../results/public-review-live-01/README.md), whose fourth
call was refused before execution while backend_emissions still read 16.
