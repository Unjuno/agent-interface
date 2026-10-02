# Issue #6655 T0 preregistration — incidental interface-state legacy

## H / T / D / C / U

- **H:** In a frozen multi-episode task family, inheriting a persistent incidental state delta changes a later task's independently checked correctness or downstream observation/recovery cost relative to a paired reset-to-baseline replay. Direction is not assumed. This finite synthetic T0 tests method behavior only; it is not evidence of real-interface benefit.
- **T:** Run seven synthetic case classes over seeds 1–32 (224 paired rows): helpful incidental view; harmful stale filter; irrelevant theme; required saved effect; incomplete restoration; unowned shared/external state; and task/seed mismatch. For eligible pairs, randomize inherit/reset arm order after the originating episode using the recorded deterministic seed, hold the later task contract and seed fixed, and report observation, recovery, restoration, and total cost separately. Exclude the last two state-integrity cases conservatively; score no outcome for them.
- **D:** `PASS_METHOD_SCOPED` only if a separate raw-only auditor reconstructs every row, changed field/classification, deterministic assignment, contract/seed pair, state transition, outcome and cost; detects helpful and harmful controls; observes no downstream outcome difference for the irrelevant control; preserves the required effect in both arms; excludes incomplete/shared/mismatched cases; and rejects every frozen mutation. Any discrepancy is `HOLD_AUDIT_INTEGRITY`. No threshold or causal claim is revised.
- **C:** A hand-authored finite oracle may overfit these cases; restoration cost can change total sequence cost even when downstream outcomes do not; different task choices and reset definitions can reverse effects.
- **U:** Only synthetic state, 32 deterministic seeds, and seven authored cases; no GUI/application, model, real settings, user, or external effect. This cannot estimate prevalence, human preference, causal carryover on a real app, or T1 benefit.

## Freeze and one-shot boundary

- Base main: `762bb46b5037a2cd4a09672a2e130760a96ff669`.
- Candidate: `candidate.py`; independent auditor: `audit.py`; fixed input: `fixture.py`; construction tests: `test_t0.py`.
- Freeze file records exact source SHA-256 values, runtime, seed range, case list, and output paths.
- Construction tests run before candidate invocation; the formal candidate may run once and the independent auditor once, only after fresh main/source/path checks. Retries, replacements, parameter tuning, and output overwrite are forbidden.
- This T0 is deterministic standard-library CPU work, so no container/GUI/runtime semantics are under test and the shared container lane is not consumed. No GPU is relevant to this finite arithmetic/oracle test.
- Candidate writes to a previously absent path. The auditor reads only the frozen raw record and writes a distinct absent path.
