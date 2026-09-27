# Pre-merge review — engineering #4336

Same-author scoped review, not independent human approval.

## Scope and implementation
The new static module uses existing expansion functions and the pure validator.
It never invokes dispatch, open_session, a native backend, a clock admission check
or input. The sibling package imports are existing pure API/selector definitions;
actual native modules remain lazy. The observed36-process import/event records
support that limited claim, not an unbypassable security sandbox.

The current parser/main command and existing files are untouched. Invalid field
shapes, source index recovery, operation caps, unknown fields, no payload echo,
file errors and static-versus-live authority have focused tests. The command is a
separate module, not newly registered in the main CLI or MCP host. The unhashable
field exception becomes a generic invalid response; no core acceptance rule is
changed. Public JSON parsing is intentionally not a new strict-ingress contract.

## Packaging review correction after initial green CI
The first evidence workflow tied all historical source hashes to the current
checkout, which would unnecessarily block future unrelated runtime changes.
The posthoc verifier now has explicit --historical-only mode for CI. It still
requires every frozen research/fixture/auditor byte to match and reconstructs the
historical records, but reports current runtime/workflow drift separately.
Current static-validation unit tests run independently in that workflow. Default
local verification remains strict. No frozen source, expectation, scientific
auditor, control or36-case result was modified.

Four posthoc delivery checks passed in fresh temporary copies: strict runtime
drift refusal; historical runtime drift reported without changing historical
outcomes; changed frozen auditor still refused; altered archive refused. These
are packaging tests, not additional engineering samples or an audit-gate waiver.

The original failed large-text transfer remains in Git history and its explicit
failure record; only exact checked parts are used. The original36-cell development
aggregate is available in the conversation bundle, not the GitHub capsule. No
previously blocked l2p7 source or capsule was resent.

## Merge boundary
Require exact-head dedicated unit/evidence CI and relevant existing CLI, portable,
X11 and MCP checks before qualification. Any queued run is not a completed gate.
Keep historical evidence success separate from current runtime tests and from GUI,
model, performance or global-roadmap success. Parent #3850 remains open.
