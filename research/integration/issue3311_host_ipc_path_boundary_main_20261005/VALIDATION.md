# Latest-main regression validation

Executed from the root of branch `research/3311-host-ipc-boundary-20261005`,
based on `origin/main` commit `2f2c83c3da36566bac410b13b2ed5202c9641f1a`:

```sh
PYTHONPATH=research/live_control python -m unittest \
  research.live_control.test_adaptive_acquisition_caller_v3 \
  research.live_control.test_deterministic_invalidation_injector_v1 \
  research.live_control.test_executor_v12 \
  research.live_control.test_release_delivery_v1 \
  research.live_control.test_post_model_target_revalidation_v1 \
  research.live_control.test_openttd_effect_decision_v1 \
  research.live_control.test_evidence_target_authority_v1 \
  runtime.core_v1.test_compiled_gui \
  runtime.test_docker_schema_preflight_v1 \
  research.live_control.test_integrated_efficiency_runner_injection_v1 \
  research.live_control.test_integrated_efficiency_docker_candidate_v1 \
  research.live_control.test_docker_model_call_backend_v1 \
  research.live_control.test_docker_host_ipc_path_resolution_v1 \
  runtime.test_host_model_ipc_broker_v1
```

Result: **131 tests passed** (`focused-tests.stdout.txt`). `git diff --check`
also passed. The execution environment had `jsonschema==4.25.1` installed from
`runtime/requirements-docker-schema-preflight.txt`.

The boundary evidence manifest was regenerated after audit and verified by
`verify_evidence_manifest.py`; its captured output is
`manifest-check.stdout.txt` (`evidence integrity 32/32 PASS`).

These tests are component and inert local-process checks. They do not execute
Docker, a real model, or a desktop task and do not satisfy the outstanding
Issue #3311 three-arm allocation.
