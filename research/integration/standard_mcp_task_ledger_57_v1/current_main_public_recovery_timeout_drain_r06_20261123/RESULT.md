# R06 result: failed diagnostic harness assumptions

Disposition: **FAILED_TEST_DESIGN** in both normal and `-O` (exit 1). Both logs reached the successful observation report but the test incorrectly required `call_id` inside that report; exact call IDs are returned by the separate `interface_results` envelope. The test's `finally` block also invoked `interface_close` on a one-shot server that does not register that tool. R06 is not scored as a cleanup pass.

The trace confirms the artificial caller wait expired while the callback Future was still pending; after releasing the event, the same Future returned a response before the incorrect call-ID assertion. The test did not verify raw report finalization or exact call readback. The normal run also incurred a much longer startup/teardown interval, so the test's synchronization assumptions need loosening. Keep both failures in the record and do not retry them.

Raw logs and actual exit files are retained. This is test-design evidence only, with no product or reliability claim.
