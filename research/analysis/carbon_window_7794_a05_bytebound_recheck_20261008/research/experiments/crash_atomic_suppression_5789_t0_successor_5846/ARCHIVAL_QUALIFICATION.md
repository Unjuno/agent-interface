# Archival qualification: allocation-01 start-gate STOP

This append-only qualification permits preservation of PR #5896's original
13-file package. No source, plan, freeze, receipt, or historical checksum entry
is changed. This is a terminal provenance STOP record, not a scientific result
or a newly executable allocation.

## Allocation-01 remains terminal

Allocation `crash-atomic-suppression-5846-t0-20261001-01` remains
`STOP_MAIN_ADVANCED_AT_FORMAL_START_GATE`: frozen preparation main
`56ef267db50a8937f04d940a425b2b1819f714fb` differed from observed start-gate main
`fc1f06474149d81989099e5220c7aa197c142c6a`.
Candidate/auditor/container/guest counts remain 0/0/0/0 and retries remain zero.
The authoritative retained receipt is `results/5846-01/PREFLIGHT_STOP.md`.
No formal raw or audit outputs exist because neither was invoked; absence of
those outputs is consistent with this pre-candidate STOP, not a scientific pass.

The original 19/19 host construction checks are historical construction
evidence only. This archival qualification did not rerun them or invoke any
package candidate, auditor, container, guest, or source capsule.

## Original Draft condition and distinct allocation-02

The PR body asked to remain Draft until separate allocation-02 was completed
or terminally recorded. Its terminal record is now present in
[Issue #5846 comment 5930847679](https://github.com/Unjuno/agent-interface/issues/5846#issuecomment-5930847679)
and [PR #5931](https://github.com/Unjuno/agent-interface/pull/5931), under the
distinct `_5846_02` namespace. Both record a pre-candidate main-drift STOP with
candidate/auditor counts 0/0. The owner comment labels it
`STOP_MAIN_ADVANCED_BEFORE_CANDIDATE`; PR #5931 labels its retained outcome
`STOP_MAIN_ADVANCED_AFTER_FINAL_FREEZE`. These are retained source wordings,
not evidence of two invocations or a successful experiment.

This satisfies only the temporal condition for reviewing allocation-01's
archival disposition. It does not merge or approve PR #5931, transfer an
allocation, permit a retry, or infer a scientific outcome. Allocation-01 and
the predecessor #5795 `STOP_FORMAL_ARGV_MISMATCH` remain unchanged and consumed.
[Issues #5846](https://github.com/Unjuno/agent-interface/issues/5846) and
[#5795](https://github.com/Unjuno/agent-interface/issues/5795) remain open;
the process-crash hypothesis remains untested by these formal allocations.

## Byte custody and manifest coverage

Static verification at original head
`2347e96eb00e8fcb99f65eb090d57cf854d545f0` confirms all ten original
`SHA256SUMS` entries and the source/launcher identities in `FREEZE.json`.
The historical checksum list does not include `FREEZE.json`, the STOP receipt,
or the checksum list itself. `ARCHIVAL_INVENTORY.json` supplies an explicitly
current inventory of all 13 original published files, including those items;
it does not backdate their hash coverage or replace the frozen manifest.

Repository integration is preservation-only, through ordinary review and CI
gates. It grants no guest, daemon, endpoint, execution window, candidate,
auditor, runtime, GUI, model, benchmark, or product authorization. Any future
experiment needs its own distinct prospective allocation and start gate.
