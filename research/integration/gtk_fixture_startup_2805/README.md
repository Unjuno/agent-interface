# GTK fixture startup diagnostic (#2805)

This additive diagnostic follows the retained #2606 STOP
STOP_USEFUL_FIXTURE_TIMEOUT. It does not send GUI input, invoke the eight-case
matrix, or claim effect correctness. It captures Xvfb readiness, fixture
stdout/stderr, process exit, DISPLAY, metadata creation, and elapsed time.

Decision:
- PASS_GTK_FIXTURE_STARTUP_DIAGNOSTIC when the X socket is ready and the exact
  fixture emits metadata while remaining alive.
- STOP_GTK_FIXTURE_STARTUP otherwise, with retained stderr and exit codes.

Only a separately frozen formal allocation may follow a diagnostic PASS.
