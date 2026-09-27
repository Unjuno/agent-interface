# Existing stdin caller: primary-assistant use

No new production API was needed. `agent_exchange.py --native --review compact
--request -` already accepts caller JSON directly. The primary assistant used it
through PowerShell UTF-8 stdin into WSL, eliminating three separate caller-file
creation tool calls. Native immutable request-N.json publication remains intact.

Same Calc/Inkscape seeds991111/991112 and three action policies as
native-combined-batch-01. `compare.py` verifies equality except source_sequence:
1→1,7→7,11→10. Every transition was viewed before the next decision.
Both saved-file scores passed: A1=190/A2=676, rectangle x86/y50/40×30 with no
transform. Three verified releases, owner89423 exit0 and tracked cleanup complete.
All feedback statuses remain needs_review; final pixels retain the dialog even
though saved-file scoring succeeds. Image freshness/coherence is unresolved.
Tracked terminal processes do not imply normal shutdown or all descendants gone.

| Recorded span | File caller | Stdin caller |
| --- | ---: | ---: |
| First client start to final return |32.423s|28.565s|
| Inside exchanges |2.130s|2.188s|
| Between exchanges |30.293s|26.378s|

These are a single ordered pair from the same primary assistant, with practice,
ordering, scheduling and host/tool transport confounds. Setup is excluded and
readiness capture counts differ. No causal speed benefit, model-token saving,
first-useful-feedback latency, human-tempo result or broad correctness claim.
The concrete improvement is removal of caller-side file assembly, not removal
of native persistence. Most elapsed time still lies outside client exchanges.

Plan deviation: the pre-start plan write used the wrong host cwd and failed;
the allocation started once, and the plan was saved after setup before input.
The command error is described in PLAN.md. No restart hid this failure.
Source snapshots were captured after the run with no source changes during it.
Before the live run, exact read-only resume of the preceding final request also
succeeded via stdin; it did not submit input again.

`audit.py` checks77 frozen files, saved artifacts, image hashes, request binding,
release and recorded cleanup. `timing.py` reproduces timestamp accounting;
`compare.py` checks requests against the preceding archive. The comparison is
not an independent replicated benchmark. Extra scripts/docs/client-exchanges
are Git-tracked outside manifest scope. Frozen predecessor evidence unchanged.
