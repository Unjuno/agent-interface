# #6442 supplemental auditor v1 — bounded repair protocol

This is a construction repair plus read-only replay, not a formal candidate
allocation or a new efficacy experiment. It preserves the exact A03 source,
freeze, raw and first auditor/outcome from PR #6849. It cannot authorize a rerun.

- H: A separate exact-transcript checker can reject the legacy auditor's accepted
  zero-budget/fabricated-refusal records while accepting all immutable A03 rows
  and preserving all four comparator counts.
- T: First run corruption regressions against the unmodified legacy source, then
  implement the independently derived finite two-edge oracle. Run construction
  regressions and a separately recorded supplemental replay of original raw.
  No candidate/policy/legacy-auditor imports in the new checker. No container,
  WSLc, GPU, model, GUI, actual input or external application effect.
- D: Accept only the complete 128-pair schedule with exact row fields, declared
  integer budget 12, event count, typed epoch, policy-specific navigation and
  justified refusal/target terminal. Reject every corruption control; reject
  duplicate JSON keys before they disappear in parsing. Replay must preserve
  original successes: stable 8/8 for each, partial/revision soft/stateless 16/16
  and hard/exhaustive 0/16. No thresholds or historical dispositions are changed.
- C: An exact oracle is appropriate only because the fixture state space and
  schedule are explicit and deterministic. It would be inappropriate to require
  one authored transcript for a real nondeterministic interface.
- U: This v1 is a scoped independent analytic replay of the specific A03 finite
  schedule, not a generic hierarchy auditor or a proof of dynamic epoch recovery,
  live task effect, safety, latency or incremental soft-policy benefit. It retains
  the simplest stateless comparator tie; no additional search mechanism is adopted.

The CLI reads at most 1 MiB plus one sentinel byte, uses a fresh output path and
does not overwrite raw or previous output. Oversized input receives a prefix hash
only; it is never labeled with a full-input hash. Canonical JSON comparison keeps
boolean/integer/float distinctions. The full-file input SHA256 recorded for this
supplemental replay must equal the separately fixed input binding.

Construction tests can invoke local CLI copies with temporary synthetic/mutated
inputs. These are not the separately recorded supplemental replay and neither
kind spends the prior formal candidate allocation. Original A01/A02 STOPs and
A03 PASS_METHOD_SCOPED remain historical records with their existing limits.
