# Issue #6471 T0 — run and stop record

## Frozen allocation

- Allocation: `SPOKEN-CONTRACT-PRESERVATION-6471-T0-20261002-01`
- Frozen source/base: `67ebd3016af9ed99a5cb40a39d4d753871f51d75`
- Freeze manifest revision 2: `FREEZE.json`; exact SHA-256 identities for fixture, candidate, independent auditor and tests are recorded there. Revision 1 was superseded during preformal construction before any formal entrypoint ran; its source hashes and reason are retained in the manifest.
- Frozen denominator: 7 authored cases; formal order is candidate once, then independent auditor once only if candidate exits 0; retries 0.
- Formal decision: `HOLD_RESOURCE_WSLc_UNAVAILABLE`; candidate invocations 0, auditor invocations 0, formal retries 0.
- GitHub disposition record: [Issue comment](https://github.com/Unjuno/agent-interface/issues/6471#issuecomment-5945083400); Issue #6471 remains open.

## Executed construction check

Command: `python3 -m unittest discover -s research/analysis/spoken_instruction_contract_preservation_6471_t0_20261002 -p 'test_t0.py' -v`

- First construction attempt: exit 1. Four assertions failed because three span annotations used lowercase `send` while the authored source/transcript began with capitalized `Send`; all remaining checks passed. This was a fixture-construction defect, not a formal candidate/auditor result.
- Correction: fixed the three literal span annotations to exactly match the frozen strings. No scientific labels, expected outcomes, or formal raw evidence existed to change.
- Corrected construction attempt: exit 0, 6/6 tests passed. It exercised the seven synthetic dispositions, equal-WER setup, fail-closed invalid source span, ambiguity-to-clarification path, and absence of execution authority.
- Independent design review found that span existence did not by itself prove target/recipient/bound labels matched the linked surface text. The candidate now fails closed on those links; the independent auditor also compares complete source/transcript slot labels and source-span text to a separately authored oracle.
- The first strengthened construction attempt exited 1 because null-valued optional slots were incorrectly required to have spans. After correcting only that optional-slot handling, the strengthened suite passed 6/6. A seventh test then exercised the independent oracle against recipient, negation, speech-act and source-span label mutations; final suite exit 0, 7/7.
- Construction tests call in-memory candidate/auditor functions; they do not run `candidate.py`'s allocation entrypoint or `audit.py`'s raw-only allocation entrypoint. Formal invocation counts therefore remain zero. No `candidate.raw.json` or `audit.raw.json` is generated or asserted.

## Environment/resource stop

The exact host was macOS 26.6 arm64 with CPython 3.14.5. `command -v wslc.exe` and `command -v wsl.exe` returned no executable. The governing `docs/CURRENT_GOAL.md` requires WSLc for eligible local CPU work and disallows using Docker/OrbStack as a substitute unless the frozen protocol needs Engine API, Compose, unsupported isolation/resource controls, or GUI-specific behavior. This protocol has none of those requirements. Therefore no formal allocation was started. The shared OrbStack daemon and its containers were not touched; only `docker context ls` was queried during environment inventory.

## Claim boundary

The passed 6/6 result is construction-only and host-only. It does not satisfy the T0 decision gate and is not a scientific method PASS or FAIL. The fixtures are authored text and structured slot labels; character spans are not audio timestamps, and no ASR, prosody, source-intent truth, model proposal, human, GUI, application effect, action authority, safety, or deployment claim follows. Resume only when an eligible WSLc lane is available; do not rerun a consumed allocation (none was consumed here).
