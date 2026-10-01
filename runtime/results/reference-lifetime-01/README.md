# Guarded reference lifetime metadata

Candidate source `03587c222ffc88c41108e40a7df103475c64734a` addresses the
interrupted `post-release-spine-04` failure by returning the existing finite
alias deadline. It does not extend TTL, renew an alias or retry an input.

Single mint and every successful batch reference now include `lifetime` with
the execution host's monotonic clock, mint time, actual expiry, capture freshness
limit and `authority_granted=false`. Legacy Python `mint` still returns its
offset pair. New Python `mint_reference` returns offset/lifetime together.
Pixel/focus/before-press guards, input lease and recovery requirements are unchanged.

Test-first controls initially failed because the finite metadata API and public
field were absent. Deterministic real-store tests verify expiry after 300 seconds,
explicit new-alias grounding from a fresh observation, unchanged capture
freshness/pixel refusal and legacy compatibility. A public MCP test verifies
single/batch metadata and retained lookup without renewal. Three existing batch
assertions were adapted to project their original alias/offset contract; refusal,
partial registration and no-input assertions are retained.

Local common integration runner passed **337 protocol + 149 harness tests**.
Full stdout/stderr and result JSON are included in the raw archive. Async debug
slow-task messages appeared during local execution; no tests failed.

Fresh primary self-use used the new committed portable archive on WSL3.0.1,
Ubuntu/private X11, seed1001050. The primary viewed two original screenshots,
grounded a navigation reference, opened the actual task screen through guarded
keyboard input, then grounded field/Save together. Both lifetimes were observed
with about299.97 seconds remaining using the same running server's clock.
Retained lookup returned byte-equivalent lifetime values and invoked no operation.
Seven public calls, one navigation program, 68 emissions, no Save attempts.
Independent scoring therefore reports all six tasks missing as intended.

Navigation release and public close verified empty keys/buttons; relay code0
and original fixture handle82696 exit0 were observed. Cleanup child returncodes
are retained individually. This scoped metadata pass does not replace the failed
full pair, prove model recovery policy, economic benefit, speed improvement,
cross-domain coverage or product acceptance. Those gates remain HOLD.

`raw.tar.gz` retains the pre-launch plan/source hashes, committed portable runtime
and host bundle, all original calls/images/reviews, score and terminal records,
and complete local CI logs. `verify.py` checks archive inventory/hashes and
recomputes semantic findings without Python assertions. Run normally or with-O.
The next full comparison must predefine how the primary handles pauses and
explicitly grounds fresh aliases; it must not reinterpret the earlier failure.
