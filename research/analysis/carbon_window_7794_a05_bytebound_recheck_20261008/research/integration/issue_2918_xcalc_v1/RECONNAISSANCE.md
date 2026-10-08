# Repository and coordination reconnaissance

Checked through GitHub MCP and a local fetch before formal-01; refreshed again
against the current main before this source freeze.

- Current experiment base: `0c6dd4b1aee14af5ead0a873b7190391c7a4b25b`.
- `README.md`: evidence-first research repository; completed evidence paths
  stay stable and new navigation is additive.
- `docs/CURRENT_GOAL.md`: the 2026-09-21 explicit operating direction is to
  validate concrete Issue ideas in Docker/OrbStack, freeze H/T/D/C/U, retain
  STOP/HOLD, and publish executed raw evidence through a reviewable PR. The
  broader current integration priority remains recorded separately.
- `ROADMAP.md`: higher-level priority remains one coherent desktop path and
  observation gating; the #2918 experiment is a bounded research gate, not a
  replacement for that roadmap.
- Issue #2918 was fetched directly through GitHub MCP and is open. It requires
  a real observation boundary, intent/observation epochs, binding/dependency
  lineage, frozen #1904 compiler, uncertainty controls, independent scoring,
  and a second surface or held-out workflow. Existing allocations 01–05 and
  their preserved STOP/HOLD lineage were reviewed before choosing XCalc as the
  second X11 app surface.
- GitHub MCP recent open-issue search included #2849, #3188, #3676, and #3700;
  recent closed-issue results were also inspected. Those are separate ideas;
  this task remains explicitly scoped to the user-selected #2918 hypothesis.
- GitHub MCP recent open-PR inventory included active work such as #3765,
  #3766, and #3767. Main subsequently advanced with unrelated #3783; no
  existing branch matching `issue-2918-xcalc` was found. The latest main also
  includes Issue #3628's XTEST/Tk event-witness construction; it uses distinct
  paths and tests a different event-delivery contract, so it does not overlap
  this XCalc observation/certificate transfer bundle.
  The local work uses additive branch `research/issue-2918-xcalc-v1` and only
  path `research/integration/issue_2918_xcalc_v1/`; no overlapping paths were
  found when fast-forwarding to current main.

The branch was fast-forwarded from `07858c6961fd4f2bea03fe33469817eab684780c`
through `b733488a06cf6ad6b50f170805dd0723be6c841c` to
`182cbfe7dca94b0199270dcc8e4359aecb7e336f` and then
`0c6dd4b1aee14af5ead0a873b7190391c7a4b25b` before freezing. `runtime/cli_v1/observe.py`
and the #1904 `model.py` were byte-identical across that main advance; their
current hashes are recorded in `SOURCE_FREEZE.json`.
