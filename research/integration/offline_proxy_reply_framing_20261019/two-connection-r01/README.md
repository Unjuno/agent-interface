# Same-PID two-connection relay discriminator r01

This additive local test isolates one remaining false-gating risk from the
A03 framing diagnosis. It creates separate identity and input socket relays
with the same synthetic owner PID and deliberately colliding connection-local
reply sequence numbers. The identity-channel pre-press reply is forwarded; an
input-channel sync reply is held only after its own XTEST KeyPress and matching
synthetic event receipt. The input relay then retires at its finite test
deadline as `UNKNOWN`, with no task-success or replay claim.

The 28 parser/policy/socket tests pass in normal and optimized Python. The
standard-caller relay composition suite passes 3/3 in both modes. Its main
blocked-input case now runs the caller's `TargetQueryWorker` process-identity
read through a distinct identity `FakeSocketRelay`, servicing three sequential
query/reply transactions (reply sequences 3, 5, 7) before the input KeyPress.
The identity connection's parser records no input target; the separate input
connection holds its own matching reply and retires as `UNKNOWN`. A second
caller case changes the fixture generation and confirms the actual caller
query path rejects it before either relay sees a KeyPress.

The `X11TargetQueries.read` and `read_linux_x11_process_identity` code now run
in the standard caller. A Fake XRes connection supplies shaped version/client-
ID responses and a `/proc/<pid>/stat` fixture; PID 123 produces a stable source
generation and changing the marker to PID 124 produces a different digest that
the caller refuses before press. The socket adapter separately sends synthetic
NoOperation/GetPointerControl frames as transaction markers and carries their
colliding connection-local replies through the second relay; these frames do
not encode the XRes operation itself. This exercises caller→query-worker→
identity-socket integration and the real generation hashing/validation logic,
but does **not** exercise XRes wire encoding, server PID discovery, live server
ordering, or physical release. No A02/A03 allocation was reused. No live X server,
WSLc/Docker, GUI, OS input, or model was used.

Run the four commands in `conditions.json` from the repository root. Their exact
shell outputs are retained as compressed raw files; `seal.py` checks the output
status/count and writes a source/result SHA-256 manifest. Two initial
experiment-runner bootstrap failures (`ModuleNotFoundError` before any test
ran) are retained separately as `runner-import-failure*`; that harness used a
working directory one level above the checkout. The four commands were then
run directly from the repository root and their outputs passed the
count/status checks. focused normal and `-O` stdout receipts (`test-output.raw.gz`) plus identity transaction
records for held-input and stale-generation cases are in
`caller-identity-r01/`; the manifest covers all files there.
The next finite step is to exercise XRes request/reply encoding and decoded
client-ID values over the query connection, while preserving the existing
UNKNOWN/late-request behavior. Physical release and a WSLc-backed result remain
open; WSLc still requires verified ownership and unused allocation evidence.

A first integration attempt serviced only one identity query and timed out on
the caller's subsequent focus/input guards. The fixture was corrected to serve
consecutive query frames with connection-local reply numbers; the updated
caller composition then passed and verified three pre-press replies. A later
composition upgraded the reader adapter to call the actual `X11TargetQueries`
and process-identity implementation against shaped synthetic XRes/PID data.
The first attempt was a harness defect, not a product failure, and is retained
here so the fixture limitation is clear.
