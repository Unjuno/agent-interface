# Local runtime validation

Validation used the pinned OrbStack image and current-main checkout. No runtime source was
modified by this study.

## Targeted tests

Before formal execution, `runtime.cli_v1.test_golden_v3` and
`runtime.cli_v1.test_native_golden_boundary` passed **16/16**. This is the targeted test set for
the runtime entry point used by the allocation.

## Broader suite attempt

The broader `unittest discover -s /repo/runtime` sweep discovered 240 tests: **12 failures, 13
errors, 1 skipped**. This is an environment/inventory-limited local suite result, not a clean CI
PASS and not a failure of the formal allocation. Retained log:
`ci/full-runtime-suite.log`.

Observed blockers include unavailable `mcp` and `jsonschema` Python modules, source/test paths
omitted from this sparse checkout (`research.integration.golden_v3_receipt_composition_2916` and
`integrated_efficiency_app_server_model_v1`), and no `git` executable inside the pinned container
for distribution-build tests. Schema-preflight tests consequently reported
`STOP_SCHEMA_VALIDATOR_UNAVAILABLE`. A focused 54-test run over core, selector, X11 integration,
and golden boundaries passed 53 tests but the X11 Tk fixture could not start in this image; its
class setup exited before any X11 integration case ran. See `ci/focused-runtime-suite.log`.

The first discovery invocation used a top-level `-t /repo` path that unittest rejected as
non-importable because this source set has no `runtime/__init__.py`. It failed before test
discovery (0 tests); retained separately as `ci/discovery-setup-error.log`. Removing that option
allowed the broad sweep above. No test failures were discarded or rerun with altered source.
