# Formal allocation 04: interface-preflight STOP

The required no-GUI schema preflight started in the pinned, network-disabled
ARM64 container, but the AST evaluator supplied only the dynamic `window`
binding and omitted the runner's `SURFACE` constant. It exited 1 with
`NameError: name 'SURFACE' is not defined` before calling the runtime validator.

**Disposition: `STOP_PREFLIGHT_AST_EVALUATION_NAME_ERROR`.** The stop gate
worked as specified: Xvfb and Chromium were not started; GUI actions and model
calls were zero. This says nothing about whether the runtime accepts the
interface. Formal-04 is not retried. The next successor must supply the exact
fixed surface value to the evaluator and verify all free names before
evaluation, while preserving this result unchanged.
