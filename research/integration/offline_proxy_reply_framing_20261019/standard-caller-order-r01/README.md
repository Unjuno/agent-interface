# Standard-caller Fake X request-order regression — R01

The previous full CLI run stopped in `test_saturated_relay_stdout_dispatches_cancel_to_held_fake_x_caller`: the caller's key chord sends XTEST KeyPress, matching KeyRelease, then `GetPointerControl`, but the offline parser candidate discarded the press association at KeyRelease. That prevented the synthetic reply from being held and left teardown waiting on the Fake X owner.

The candidate now retains the association through a matching KeyRelease until the next synchronization request, while a nonmatching release or unrelated request clears it. The composed Fake X server consumes and validates the release frame and responds with the sync request's actual sequence. This is a test-only parser/caller path; it does not connect to an X server or prove platform input release.

The lifecycle race assertion accepts either valid scheduler outcome: the first key press crossed the race before lifecycle retirement, or it was refused after retirement. Both require terminal KeyRelease and an empty local held-key set. A supervised Win32 test uses a five-second lease so it tests cancellation drain instead of subsecond worker-start scheduling, waits for the atomic report write before deleting its temporary directory, and bounds the serialized close drain at two seconds.

## Verification

See [CONDITIONS.json](CONDITIONS.json) for exact commands and environment. The full CLI suite passed 593 tests with 8 skips in normal mode. The focused parser, relay, public-caller composition, supervised Win32, and lifecycle set passed 48 tests in both normal and optimized Python. Raw stdout is retained in the three `raw-*.log` files.

The initial full-suite failures were a subsecond test lease, a 150 ms close drain window, and the lifecycle race's overly specific emission order; one Windows temporary-directory cleanup error also exposed that the test returned before its atomic report was finalized. These were diagnosed and corrected in test synchronization/expectations. The final full run passed.

No WSLc allocation, Docker/container/image operation, native GUI input, real X server, model/provider, or live experiment was used. This does not establish WSLc portability, MAP01 task effect, bounded native release under platform I/O blockage, matched efficiency, or broad reliability.
