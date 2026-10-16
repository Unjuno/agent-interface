# #5156 owner key-up caller-boundary gate

## Scope

This is a pre-construction control-flow audit for allocation
`MAP01-OWNER-KEYUP-BRACKET-5156-20260928-01`. It does not modify or import the
owner at runtime and does not consume the separately registered X11 fixture
allocation. It tests whether the proposed universal caller/RPC nesting rule is
even satisfiable for autonomous owner-loop cleanup.

## H / T / D / C / U

**H.** When expiry, cancellation, focus loss, stop, or thread exit causes the
InputOwner loop to call its local `release(reason)`, that KeyRelease is not
enclosed in the client-side v3 `InputOwner.call` timer. Therefore the universal
nesting rule cannot cover both explicit `up` calls and autonomous cleanup under
the currently pinned interface.

**T.** At exact main `16421aefa2ec357b79e3fd3dc307b32955bc6fab`, verify source
blob and SHA-256 identities, parse the v10 `InputOwner.call` and `_run` plus the
v3 caller wrapper, enumerate every local `release()` call site, and independently
audit those findings in a second implementation. Run six deterministic source
controls. No owner code is executed; no X11, Docker/OrbStack, model, GPU, input,
or network workload is used.

**D.** `PASS_AUTOMATIC_RELEASE_OUTSIDE_CALLER_BRACKET` if at least one autonomous
release call site is reachable from `_run` without an enclosing call to
`InputOwner.call`, while the v3 timer exists only around caller-invoked
`up`/`button_up` or `release`/`close`. `FAIL_CALLER_BRACKET_ALWAYS_PRESENT` if
all release sites are necessarily within an active caller timer. Source/hash,
parser, or classification ambiguity is `STOP_SOURCE_OR_AUDIT`.

**C.** Frozen main/source blobs; two independent AST traversals; no source edits,
runtime execution, or timing samples. Explicit caller requests and automatic
owner-loop cleanup are classified separately.

**U.** This determines call-boundary availability only. It does not measure
XTest request timing, XSync completion, physical key state, application
consumption, or task outcome. A PASS means the original universal nesting rule
must be scoped to explicit caller `up` operations or redesigned before a fresh
formal registration; it is not a key-up telemetry result.

## Frozen identities

- `research/live_control/input_owner_v10.py`: Git blob
  `341b3c01649943ddaad5f28431a792c4889cc36e`, SHA-256
  `ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b`.
- `research/live_control/input_transition_owner_v3.py`: Git blob
  `0ea631abcf6272f0538a9ef9198ad8069b47b464`, SHA-256
  `5ffdbb3679451fefdc3836917d43d924f0f43c8082d21327207ecefbd87f5be6`.

## Reproduction

From the repository root:

```text
python -B research/live_control/owner_keyup_bracket_5156_v1/analyze.py
python -B research/live_control/owner_keyup_bracket_5156_v1/verify_result.py
python -B -m unittest discover -s research/live_control/owner_keyup_bracket_5156_v1 -p 'test_*.py' -v
```

These commands are host-only static checks. They do not authorize the later
X11 fixture allocation.
