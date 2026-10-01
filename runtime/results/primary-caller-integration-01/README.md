# Public primary caller integration

Source `9e8bcd01ba61058ddac7f4a7c7b76b60e1626f26` adds the opt-in
`runtime/host_v1/primary_caller.mjs` and includes it in the committed portable
Node host bundle. This integrates the actual spine08 caller policy into the
public host layer, while preserving every frozen spine07/08 file and failure.
The branch was checked at1354e7741; current-main40885011 was fetched and reviewed
at intake. No current-main promotion is claimed.

The research failure in PR#5691 showed a malformed first reply throwing during
envelope extraction while caller STOP remained null, allowing a second effectful
dispatch. The integration regression reproduced missing STOP against the actual
spine08 caller. Response extraction and outcome validation now share a catch
boundary that latches STOP before propagating the original exception. Catching
the exception cannot permit another ordinary tool call; public close remains
available. Empty/non-JSON/non-object normal metadata also stops. Unexpected MCP
errors can contain free text: their original response is returned after STOP,
preserving the prior evidence-delivery contract. Exact declared no-input refusal
controls preserve the original text/image/error status and remain one-use.

The `observe()` helper sends the same fixed no-target guarded-observe request
for initial and fresh observation. Accidental helper arguments stop locally
before sending anything. Direct observation uses explicitly provided target,
frame and region snapshotted at construction. This addresses the concrete
spine08 erroneous `target` argument without automatic expiry renewal, reference
minting, replay, action selection or authority. The helper is not proof of fresh
visual grounding; the primary must still view and attribute the actual image.

Fourteen public primary-caller cases cover malformed envelopes/metadata,
original extraction and transport exceptions, free-text MCP errors, release
validation errors, repeated no-target observe, argument rejection, direct scope
snapshot, normal completed neutral results and actual host text acknowledgment.
The complete CI Node invocation passes **72 tests**. Five prior caller regression
files adapted to import the public module plus14 new cases pass **19 tests**.
The final shared Python runner passes **337 protocol +149 harness tests**,
including committed host-bundle identity. Full logs are retained.

One intermediate regression run failed in `test-baseline-policy.mjs`: strict
JSON parsing threw on the original free-text `Unknown tool` MCP error. Its full
output is preserved. The additional regression first failed, then the original
error-return contract was restored with STOP already latched. The first
malformed-envelope red/green logs are retained too; not every intermediate tool
console output was written to a separate file. No failing run is described as
passing or as a formal benchmark allocation.

The fresh source-pinned bundle was consumed from `/tmp`, outside the checkout,
using its public primary caller and instrumented host with an inert child
transport. Two `observe()` calls sent `{}` to `interface_guarded_observe`; public
close followed. All three original text replies were acknowledged; original
transport exited0. This checks packaging and composed host use, with **no GUI,
physical input, real capture, model decision, input release or task-success
claim**. The raw consumer requests/replies/events/receipts remain available.

`raw.tar.gz` includes committed implementation snapshots, actual baseline,
red/green and failed/final regression logs, full shared Node/Python logs,
source-pinned portable runtime/host manifests and actual bundled consumer
records. `verify.py` in the archive checks source/bundle hashes, final result
counts, original consumer response/presentation/text identities and no-input
request sequence. Extract into a fresh directory and run `python verify.py`.
This is integration/maintenance verification, **not** the separately proposed
Docker scientific successor in Issue#5693; that issue is not closed by these
tests. It does not establish live uncertain-delivery behavior.

Next use this public caller and observe helper in a newly frozen primary GUI
allocation. A new complete guarded/direct pair, current-main adoption, compiled
baseline, domain coverage, measured provider tokens/cost and human tempo remain
pending. Full product goal and integration gate remain HOLD.
