# Candidate partial-startup auditor branch

Bounded successor change for E03's missing-imports audit gap. Not an E03
official-auditor retry or substitution. No native experiment or fresh Issue.
Before a future separately frozen formal audit, add a validated partial-cell
branch before opening imports.json. If it accepts, return verified STOP,
scientific_pass:false, exposure:NOT_ESTABLISHED; do not enter success path.
Otherwise reject incomplete evidence, or use the separately reviewed full
exposed-cell auditor when imports exist. This helper alone does not dispatch
or verify the full audit: runtime/source/export/container custody and executed
case prefix/first-stop rule must be checked by the outer auditor.

Requirements: literal false outcome/release gates, failed natural child
terminal, empty stdout, nonempty stderr/fatal, ordered integer clocks/process
identity, recorded child argv, empty cleanup faults/unhandled errors, no
imports and no declared exposure fields. Missing imports alone grants nothing.
This validates saved record consistency, not independently proving no live
input/game happened. Existing E03 official FAILED_NO_PASS remains unchanged.

TDD method unit: constant permissive stub accepted32 invalid subcases,
retained PARTIAL-RED.log. Repair enforces explicit type-sensitive guards,
normal/optimized package tests run without producer/game/auditor replay.
Actual saved E03 row is a read-only compatibility fixture only; output is
construction compatibility, never retrospective official audit PASS.
Future formal E04 remains0; full source/runtime/case-prefix audit integration
and independent review remain necessary. No wrapper-only PR/Issue warranted.
