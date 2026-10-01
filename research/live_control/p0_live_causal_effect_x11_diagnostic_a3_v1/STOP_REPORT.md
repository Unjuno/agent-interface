# #1310 preformal diagnostic stop

Disposition: `PREFORMAL_SETUP_STOP_EFFECT_CHILD_TIMEOUT_DIAGNOSED`; scientific disposition **NONE**.

- construction2 / formal0 / reruns0
- control child complete and clean
- V12_EFFECT child timed out after 8 seconds
- returncode unavailable because timeout; stdout/stderr empty
- no effect science row was written or reconstructed
- case directory existed but contained only its empty Xauthority file
- failure-tolerant aggregate was written successfully
- final related process/socket residual0

The observability factor succeeded: unlike #1301, the stop is now explicitly classified as an action-child hang rather than an unknown aggregate failure. The next one-factor harness discriminator is a timed Python faulthandler stack dump inside the child. It must not modify the exact science runner/action/effect/scorer path.
