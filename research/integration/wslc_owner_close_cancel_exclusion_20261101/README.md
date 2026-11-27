# Owned close versus ordinary cancellation

This packet follows [the idle-retirement prototypes](../wslc_idle_retirement_serialization_20261101/).
The local r126 candidate extends draft #10094 at
`e6ed07edad270cc4631518bf3b53124e4ada28b6` but is not part of that PR or
main. Main at freeze was `6b117bf961675e62e1963377eaddae466bcdada4`.

Controlled parent-side tests found that ordinary cancellation and close could
overlap in either order. The local candidate defers close while cancellation
is in flight and refuses a cancellation after close begins, retaining UNKNOWN
rather than reporting release. Two targeted tests failed before the local
change and passed after; the candidate passed 99 selected WSLc tests in both
normal and optimized Python.

Two separately frozen private-Xvfb trials used a real spawned owner and a
prestarted cleanup supervisor. In the first, an ordinary RPC and the parent
cancellation poll were paused; close deferred and did not close the supervisor
at that point. Once resumed, the old cancellation and cleanup remained
UNKNOWN. In the second, close was paused at supervisor closure; a subsequent
cancel returned unconfirmed/UNKNOWN, then close completed. Both arms used a
separate fresh owner to type `a` into a synthetic target and verified its
release and neutral input. The old owner held no input during the overlap.

The pauses and first arm's control timeout were injected and there was one
run per arm. This does not establish general concurrency safety, finite
recovery, physical release or MAP01 behavior. `raw.zip` contains source,
conditions, test output, reports and target events; its entries are hashed in
`archive-manifest.json`. Run `python audit.py` to verify the archive and re-run
the saved report auditor. Host-specific `private-command.json`, Python bytecode
and the Windows red-test traceback containing a local path are excluded;
originals remain local. The audit checks recorded evidence consistency.
