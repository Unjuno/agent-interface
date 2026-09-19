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
