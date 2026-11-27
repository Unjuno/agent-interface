# MAP01 Win32 expiry-caller block R241–R242 audit

## Disposition

The frozen eight-attempt block `map01-win32-expiry-caller-pair-r1-20261115`
stopped at its preregistered stop condition after R242. Its decision is
`HOLD_NO_WINNER_FAILURES_RETAINED`; there is no matched winner, no efficiency
estimate, and no completion claim for Issue #57. R243–R248 were not attempted
and must remain unattempted under this consumed block.

The private source packet is at:

`private-packets/map01_native_windows_current_main_r180_abnormal_exit_20261114/runner-candidates/r241-expiry-caller-pair/`

The block used a native Windows MAP01 target, identical 3 s lease / 120 ms
click / SHIFT-hold protocol, an 8 s wait, and delayed SHIFT-up plus second click
that were to be excluded after expiry. A was automatic monitor expiry recovery;
B was an exact-call `interface_cancel` at the retained expiry deadline. The
block intentionally made zero provider/model calls, so it cannot measure token
efficiency.

## Attempt outcomes

| Attempt | Arm / disposition | What the retained records establish |
|---|---|---|
| R241 | A — `PASS_SCOPED_EXPIRY_CALLER_ARM` | One dispatch/recovery; source status `recovered`; release receipt and both neutral horizons verified; delayed operations excluded; ammo HUD 50→49; task success null. Full lifecycle 128.224235 s. |
| R242 | B — `FAIL_OR_CENSORED` | No native action was dispatched (`preexpiry_sendinput_count=0`); exact fresh-session reconciliation returned `not_dispatched`, release false, no replay, and restored custody to clear. No task/effect arm was observed, so its 39.062189 s lifecycle is not comparable task time. |

R242 arrived at the 3 s authority deadline before producer start authorization.
The frozen stop condition required retaining this no-start/incomplete-release
failure and stopping; no replacement attempt was authorized by the block.
Custody reconciliation recorded clear at revision 842 with no pending operation.

## Source and custody limits

Both attempts used detached source commit
`4acd679181e4899f3bafca8a7162da07efaa3f58`, not current `origin/main`
(`89b6f1f03fbb897b63d65120fe19474025380bef` in this audit checkout). Runtime
source has materially changed since the frozen run. Therefore R242's startup
failure is a historical outcome of that pinned source, not evidence of a
current-main defect; and R241 is not a current-main trial.

R241's retained trial manifest has 227 entries and independently rechecked
with no missing or mismatched files. Its conditions SHA-256 is
`0949267cfdb3ba17a5d43121c119b3a9f5942d87cc809741dbf5795445dff5f3`; its
manifest-file SHA-256 is
`37a8a7377ccd348d45fce66c0737d9fdafe7ce8375156140dd2a6580df2a4724`.

R242's initial manifest has 50 entries and matches the ledger's conditions
SHA-256 `fa9a5919a4c0308a194a6a77c3910ecdad0b70f7119d3434406ad8803f1a35bd`
and recorded manifest-file SHA-256
`08d0d78358fc9b23891188bd891b642c2d312f31bacf65571ceded75a35885d0`, but
two current files (`gzdoom-stdout.log`, `instance/gzdoom.ini`) differ from
their captured digests. Seventeen additional files were added after that
manifest by reconciliation/postrun work. The separate nine-entry postrun
manifest rechecks cleanly, but covers only that subset and does not repair the
initial manifest gaps. The additive 69-entry current-byte snapshot is retained
as `r242-current-snapshot-manifest-20261117.json`; it records present bytes and
does not recover or attest earlier bytes. The raw packet remains private/local;
this public report does not reproduce its raw content.

The private README still says no attempt started. That statement was true when
written but is superseded by the later block ledger and this audit. The frozen
ledger is authoritative for schedule and disposition; historical raw records
remain unchanged.

## Current-main contract recheck

Against current-main tree `89b6f1f03fbb897b63d65120fe19474025380bef`, three
focused synthetic contract tests passed 3/3 normally (10.933 s) and 3/3 under
optimized CPython `-O` (10.373 s):

- startup crossing expiry is reported not-dispatched only after gated exit;
- public caller cancellation is rejected before expiry and recovers exactly
  once after expiry;
- an expired start gate publishes zero native actions.

Logs are retained as `current-main-normal.log` and
`current-main-optimized.log`. These tests confirm current code contracts for
synthetic fixtures. They do not reproduce the live R241/R242 pair, establish a
native current-main comparison, or measure task economics.

## Next useful boundary

Keep this block stopped and preserve the six scheduled non-attempts. A fresh
current-main experiment, if separately justified and allocated, needs a new
ID/block, independent freeze, complete raw custody, and an effect-capable
matched public-caller arm. A separate integrated #57 study still needs a trusted
allocation/usage source and matched same-model task arms with all-attempt
latency, token, resource, release, and correctness accounting. Until then #57
remains open and the overall computer-control goal remains active.

## Included derivative files

- `manifest-r241.json` — original R242 trial manifest (raw packet path in its
  entries is local and not included here).
- `postrun-recovery-manifest-r242.json` — original postrun subset manifest.
- `current-main-normal.log`, `current-main-optimized.log` — current-main
  synthetic contract recheck logs.
- `r242-current-snapshot-manifest-20261117.json` — additive inventory of the
  current R242 packet bytes, not a reconstruction of the original manifest.

