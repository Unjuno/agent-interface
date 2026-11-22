# Current-main disposition

This package preserves a historical pipe-pressure baseline and a bounded-writer repair candidate. Its frozen repair test runs the byte-pinned module under `candidate/`; it is not a verification report for the current-main implementation.

While rescuing this evidence onto current `main`, the production helper had independently evolved. Current `research/doom/doom_controller_failure_cleanup_v1.py` uses a nonblocking POSIX pipe write with `select` and a monotonic deadline, then continues owned-child retirement and records additional input/reader/terminal receipts. Replacing that implementation with the historical daemon-writer candidate would discard current-main behavior, so this rescue keeps the candidate and its original test/evidence inside the research package and does not modify the current helper or its integration test.

The frozen result supports the constructed finding that a full child-stdin pipe can strand synchronous failure cleanup, and that the tested candidate avoids waiting indefinitely for that write. It does not independently certify current-main runtime behavior, physical input release, process-family cleanup, or a universal deadline. Any new regression against the current helper should be a separate, current-main-pinned test and must not rewrite this package's frozen artifacts.
