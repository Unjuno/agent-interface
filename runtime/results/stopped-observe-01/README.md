# Explicit observation after sticky primary STOP

Local candidate stacked on PR #6077; not yet adopted on main.
Implementation frozen at 4dced48b32a439c52d2c9aea10954cdc2035cfb4 before
one live allocation (seed 1001070). Archive SHA256:
44a6d0f0c60ef5ffd7b0faa096c69e05995e1fa803cb0cbe409d6ed7d655d637.

Previously a completed Save with a pending application cue stopped the primary
caller and also prevented an explicit fresh screenshot. `observeAfterStop()`
allows exactly one read-only guarded observation per explicit invocation, with
no arguments, while retaining STOP. Ordinary input, mint and observation remain
blocked. No automatic polling, input replay, remint, session restart or authority
recovery is added. Host transport/evidence refusal can still deny the observation.

The primary used the packaged Node caller/host, packaged Python relay/public MCP
server and native X11 against a private Tk application in Ubuntu/WSL. Initial,
pending and later Saved PNGs were actually reviewed. After all owners/children
were terminal, independent app records showed exactly one Save of t1001070 and
one Saved acknowledgment 3001.003 ms later. Pending source sequence 6 preceded
the acknowledgment; explicit observation sequence 7 followed it. STOP remained
`unexpected MCP refusal` through close. Five public requests, three primary
images, seven captures, one native input program; no remint or retry.

The later screenshot was captured 24056.836 ms after the acknowledgment, while
the app clock continued through primary review. This establishes functional
inspectability without duplicate input; it does not establish fast semantic
awareness, latency improvement, human tempo, or reduced tokens/cost. Model usage
and billing are not attributed in this report. No comparative baseline is run.
No live second-input attempt was made: pre-dispatch input blocking and resistance
to a fourth-argument escape are checked by the production caller unit tests.

Initial RED and full 129 passing host tests are retained. The shared local native
CI runner also passed; its full protocol/harness logs and result are retained in
local-native-ci. This is local contract coverage, not remote CI completion.
`python3 verify.py`
and `python3 -O verify.py` check original host metadata/error flags, exact primary
PNG bytes and declared hashes, same session, command order, sticky STOP, app
event/capture ordering and native operation counts. Six in-memory counterexamples
must be rejected (cleared STOP, duplicate Save, wrong token, read-only dispatching
input, stale capture and extra public request). They do not rerun or modify the
live allocation. `audit.json` records those finite checks, not a broad safety proof.

Decision: retain the explicit read-only helper as a local integration candidate;
hold performance claims and remote publication until parent PR #6077 resolves.
Raw frozen scaffolds, images, requests/replies, app events and cleanup are retained.
