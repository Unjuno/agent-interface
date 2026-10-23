# R33 preparation and custody

R33 starts from main `ea20642b35a11621fa94e2b90523dab07f7b3c88`. The input-free preflight pins R32 raw/audit/trace hashes and semantics, all runtime and packet source hashes, the absent LowLevelHooksTimeout registry value, and fake wrapper/backend behavior.

Before dispatch cancellation, the injected Q-down callback must return and a separate process must read Q-down=true twice while the fixture generation remains unchanged. The one held callback is the first injected Q-up. After a single cancel, a second independent readback starts at 700 ms and must complete after the traced recovery Q-up SendInput return but before the 1250 ms hold ends. This tests whether a real pre-existing down state clears while native callback I/O is held.

One owned fixture, one public dispatch, at most one cancel, no replay/retry, no text input, no registry mutation, bounded hook self-release, foreground restoration. Any failed baseline gate stops before cancellation and remains FAIL_OR_UNKNOWN. Runtime `task_success` must remain null.
