# Partial owned-start allocation cleanup: r553

Eleven direct owned-session tests passed in both normal Python and `-O` in
separate isolated Linux containers. They include injected failures while
allocating the second pipe, RawArray and Process object, and a close failure
after a pipe was returned. The candidate attempts to close each obtained
connection, preserves a reference and error type when close raises, and refuses
verified close while that cleanup remains unconfirmed. The tests use Fake X or
mocked allocation failures; they do not measure actual OS failure frequency.

Retaining an object does not prove its underlying descriptor remains open or
closed; a close-then-error cannot be safely retried by number. A separate later
mock check covers this ambiguity, but is not part of the archived 11-test runs.
Cleanup interrupted by BaseException, resources hidden inside a failed Pipe()
before it returns, GC/process-exit custody, existing owner/supervisor cleanup,
and actual input release remain unresolved. The separate MCP shutdown custody
regression remains failing, so the candidate must not be treated as complete.

`raw.zip` SHA-256
`57d3676e96baebc9c03091284901451204c1bd11716bc2e6cda921880226e1f0`
contains pre-run conditions, base, diff, status, both test outputs and exit
codes. Member integrity was checked. Image digest and Docker settings are
recorded conditions, not independently attested by unittest output.
