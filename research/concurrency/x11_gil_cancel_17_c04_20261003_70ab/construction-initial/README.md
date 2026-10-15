# Issue #17 private X11 construction

PASS_CONSTRUCTION: private Xvfb Shift_L keymap observed neutral, held, neutral. Formal cases: 0. This establishes a virtual key-state measurement substrate only; cancellation, GIL isolation, real desktop task effects and hard deadlines remain untested.

First package-build command exited 1 because Xvfb does not accept -version. The failure is preserved. Dependencies were subsequently confirmed with dpkg-query and actual server startup; apt installation was not repeated.

Pinned image: sha256:f9b71334f027006dd318eb947a40358f02118657641b35611fa360fcdb74637f. CPU cgroup 25000/100000, memory 128 MiB, swap 0, pids 32; private Unix socket, network disabled. Own containers exited, no active containers before release, own VM stop returned 0. Source, raw, commands and receipts retained.

Next step: bounded dedup and preregister a distinct thread-versus-process cancellation comparison using this substrate and the native in-call boundary helper. Do not replay consumed C01/C02 allocations. Main writes: 0. Goal remains active.
