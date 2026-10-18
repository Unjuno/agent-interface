# Key admission-to-release binding A01 — construction test

## H / T / D / C / U

**H:** A bounded release auditor can associate each admitted key press with exactly one later per-key up outcome using an explicit admission ID and execution context, while refusing duplicate IDs, cross-execution IDs, up-before-admission, missing up, duplicate up, and release without verified empty state.

**T:** With no GUI, model, host input, or runtime changes, execute a frozen synthetic contract fixture in pinned `python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`. The candidate reducer evaluates a baseline plus six one-fault mutations. A separately written auditor reconstructs expected decisions directly from frozen inputs and outputs without importing candidate code. Source is read-only; network is disabled; CPU=1 and memory=512M. This tests measurement-contract discrimination only.

**D:** `PASS_METHOD_SCOPED` only if the baseline passes, all six injected faults are rejected with the preregistered class, output hashes agree with the independent auditor, and both scripts compile. Any fault accepted or baseline rejected is `FAIL_METHOD`; source/image/runner/auditor ambiguity is `HOLD`. No empirical, runtime, physical-input, feedback-usefulness, recovery-benefit, MAP01, or safety claim follows.

**C:** The fixture may make identity and ordering easier than a real asynchronous producer; explicit synthetic outcomes do not prove the runtime can emit trustworthy receipts. An aggregate empty-state receipt can conceal a lost/misbound per-key event.

**U:** No actual key-up, physical occupancy, task effect, helpful feedback, recovery, model latency, timing, or live threat response is measured. This is a construction discriminator that must precede—not replace—a matched live test under separately confirmed authority.

## Frozen inputs and expected cases

The canonical fixture has one execution and one admitted `Down` key. The valid sequence is admission(`adm-1`, execution `exec-1`, step 2) → per-key up(`adm-1`, same binding) → execution-scoped verified-empty release. Seven cases are frozen: baseline; duplicate admission ID; cross-execution up; up before admission; omitted per-key up; duplicated up; and terminal release lacking verified empty input. Only one mutation is applied per case.

Image config identity: `python:3.12-slim`, image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`, repo digest `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`.

## Result boundary

Development construction only, scoped to the authored receipt contract. No allocation, runtime implementation, historical evidence, or live result is altered or implied.
