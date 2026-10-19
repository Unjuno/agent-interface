# Same-PID two-connection relay discriminator r01

This additive local test isolates one remaining false-gating risk from the
A03 framing diagnosis. It creates separate identity and input socket relays
with the same synthetic owner PID and deliberately colliding connection-local
reply sequence numbers. The identity-channel pre-press reply is forwarded; an
input-channel sync reply is held only after its own XTEST KeyPress and matching
synthetic event receipt. The input relay then retires at its finite test
deadline as `UNKNOWN`, with no task-success or replay claim.

The 28 parser/policy/socket tests pass in normal and optimized Python. The
standard-caller relay composition suite also passes 3/3 in both modes on the
same source. That caller suite still stubs target-query protocol traffic, so
the two-connection result is complementary relay evidence, not a full
caller→identity-socket→input-socket composition. No A02/A03 allocation was
reused. No live X server, WSLc/Docker, GUI, OS input, or model was used.

Run the four commands in `conditions.json` from the repository root. Their exact
shell outputs are retained as compressed raw files; `seal.py` checks the output
status/count and writes a source/result SHA-256 manifest. Two initial
experiment-runner bootstrap failures (`ModuleNotFoundError` before any test
ran) are retained separately as `runner-import-failure*`; that harness used a
working directory one level above the checkout. The four commands were then
run directly from the repository root and their outputs passed the
count/status checks.
The next finite step is to connect the distinct identity socket to the actual
standard-caller target-query seam in a Fake X composition, while preserving the
existing UNKNOWN/late-request behavior. Physical release and a WSLc-backed
result remain open; WSLc still requires verified ownership and unused
allocation evidence.

A local attempt to connect `FakeQueries.read("process_identity")` in the standard
caller directly to a distinct second relay was also tried and rejected as an
integration result: the identity reply reached that relay and was forwarded,
but the caller did not emit the expected input KeyPress within the test window.
The report stayed `observed`/not dispatched, so no input was accepted. The
attempt did not establish caller-to-second-socket composition and is not among
the passing packet runs. The temporary caller-test modification was removed;
the passing relay-only discriminator remains the evidence boundary.
