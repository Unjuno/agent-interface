# Issue #3370 — stale-source input rejection

## H / T / D / C / U

**H.** On the real managed MCP/Inkscape path, an input request naming a prior
source sequence after a newer observation has been issued is refused before
any native input action is admitted; the task owner cleans up without replay.

**T.** Freeze main `f3562e6b84d3ee09d61428f4031ed2c886a34fe1`, runner source
`research/live_control/native_mcp_v1.py` and its imported harness at that tree,
OrbStack image `sha256:cf02676f620c6679614a311c4baee4deceb135a37cae9d6e14c39a5e8e49001e`
(`linux/arm64`), seed `991123`, and one fresh private Inkscape allocation.
One persistent MCP stdio client calls native_start (source sequence 1), then
submits the explicit read-only `interaction=observe` request at stage 1 to get
source sequence 2, then makes exactly one stage-2 click request bound to old
sequence 1. It does not retry or send a corrected action decision. After the
refusal it sends a valid read-only stage-2 observation using sequence 2, then
an explicit no-input finish at stage 3 using returned sequence 3, solely to
close the owner cleanly. No host screenshot
or model call is required for this scripted negative safety control. Network is
disabled, root is read-only, app state is private Xvfb, source mount read-only,
and only a dedicated evidence directory is writable.

**D.** `PASS_STALE_SOURCE_REFUSED_ZERO_INPUT` only if the retained MCP response
shows source 2, the stage-2 call rejects source 1 before immutable stage-2
action-request publication, the only subsequent requests are the pre-registered
observation and finish, `actions.json` is absent/empty, no physical key/button
is emitted, cleanup is complete, and the managed owner exits. Any input, stale
action-request publication, request
publication, missing evidence, or ambiguous owner state is FAIL/HOLD. A setup,
image, or MCP startup failure is a retained STOP, not a retry.

**C.** One deliberately stale source reference is the only negative input
condition; all other task/runtime/source values are frozen. This is a genuine
MCP client/server call against a fresh GUI allocation, not a unit fixture.

**U.** This covers stale source rejection only. It does not test delayed or
missing image delivery, disconnect/cancellation races, contradictory effects,
host presentation acknowledgement, model-visible timing, task utility, or
efficiency. It cannot complete Issue #3370.

## Frozen artifact boundary

All trial output is additive under `evidence/stale_source/`. Runner and audit
hashes are recorded before allocation. The independent auditor consumes retained
MCP responses, immutable requests/replies, action/effect files and cleanup/owner
records; it does not authorize the experiment.
