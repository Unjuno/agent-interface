# Pinned supervisor regression tests

Three offline tests cover refusal of a mismatched owner before readiness,
use of the verified connection by the worker, and refusal of a request naming
a different display. Each checks that cleanup is not invoked in the refusal
cases. They use mocked X11 and XRes objects and do not replace the private
Xvfb experiments in `wslc_preflight_owner_identity_20261101`.

The tests ran in WSLc in normal and Python `-O` modes: three passed in each.
Conditions include the source file hashes, pinned image and resource limits;
the kernel noted swap limits were unavailable. The runtime source is the
candidate at draft commit `bced4a0` plus the added regression test.
