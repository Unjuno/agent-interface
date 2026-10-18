# Nonformal local Xvfb check of per-key cancellation release bounds

This one-shot local WSL/Xvfb smoke used the exact #7504 owner source and the frozen #7429 v13 dependencies listed below. It exercises only an isolated test window: no ViZDoom/game, model, external provider, physical desktop input, container, or formal allocation was involved.

## Successful run

Run ID: `MAP01-V39-PERKEY-CANCEL-XVFB-LOCAL-04`, display `:99`, Xvfb `800x600x24 -nolisten tcp`. WSL reported Python 3.12.3 and PyXlib. The owner admitted key `w` as keycode 25; the focused test client observed KeyPress and KeyRelease for keycode 25. During cancellation, the per-key release bound was `[106083238040108, 106083238492203]` ns; the owner verified empty state at 106083238931599 ns and the server keymap returned false for the key. All seven checks in the raw record passed. Xvfb exited 0 and its lock/socket/process were cleaned up.

The observed client KeyRelease timestamp happened to fall inside the request-to-XSync interval in this run. That is a single Xvfb client observation, not a guarantee of application consumption. The interval is still only an X server request/processing bound.

## Preserved earlier stops

- Run 01 stopped before launching because display :96 had a lock file owned by another WSL user. The lock was left untouched.
- Run 02 stopped before launching because the first runner version checked :96 while configured for :97.
- Run 03 launched isolated Xvfb :98 and sent the key to its test window, then stopped on an incorrect assertion expecting a keycode field in the owner admission (that version reports the key name). The harness closed the owner and Xvfb; the raw result records exit 0 and lock/socket cleanup.
- Run 04 used a corrected display readiness probe and key-name admission check. It is the sole `PASS_NONFORMAL_XVFB_SMOKE` result; earlier outcomes remain unchanged.

## Source identity

Owner source: exact PR #7504 branch source blob `b590babae510c65fd3e00efaa5196f5ee7f2fd0c`, raw SHA-256 `ac354ffb2a4cfb11c739c8fc636ea63455d7b24bf4d1da8b6833256e63b9f64c`.

Dependencies: #7429 current head at run `b30fd755e68d470799e6c26f12296a97cf027df8`; raw source hashes are recorded in the run JSON. The exact local harness used for run 04 had SHA-256 `0991865fb0ac95b72fe312fb40d71ae7d74fcadcac1aacffd1bdbe87f8be982a`. Only the four raw run records and this report are archived here; the run harness is not, because it was specific to the local source layout and consumed display/run ID.

## Limits

This only validates that a cancellation cleanup interval emitted by the current PR candidate is consistent with one local X server/test-client cycle. It does not establish current-main integrated v39 behavior, physical/hardware transition time, ViZDoom or application effect, independently useful feedback, bounded recovery, survival benefit, or MAP01 progress. Issue #59 remains open.