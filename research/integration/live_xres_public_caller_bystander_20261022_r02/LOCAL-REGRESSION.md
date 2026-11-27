# Local regression receipt

Source: current main `15760a07ff774d902d9a897fe33432a2e60054ba`.

The WSL2 Ubuntu CPython 3.12.3 regression command selected the XRes supervisor and client-fence suites plus the existing public-caller Fake X bystander test:

```text
pytest runtime/guarded_x11_v1/test_cancel_supervisor.py runtime/guarded_x11_v1/test_xres_client_fence.py runtime/cli_v1/test_mcp_owned_process.py -k "bystander or (test_cancel_supervisor.py or test_xres_client_fence.py)" -q
33 passed, 46 deselected, 13 subtests passed

python -O -m pytest [same paths and filter] -q
33 passed, 46 deselected, 13 subtests passed
```

The optimized interpreter emitted pytest's standard warning that Python `assert` statements are disabled; the suites' unittest assertions still ran. Pytest lived in a task-specific WSL2 venv; application dependencies came from the existing user venv. No repository dependency or runtime source was changed.
