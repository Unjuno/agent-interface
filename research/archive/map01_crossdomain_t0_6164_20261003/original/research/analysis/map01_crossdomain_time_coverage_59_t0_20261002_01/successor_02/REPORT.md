# r133 cross-domain time-coverage successor T0-02

## Disposition

**Candidate: `HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED`. Auditor: `FAIL_AUDIT`.** The candidate output now separates the OpenTTD observer stream (263 records) from its one transition witness and retains a conservative HOLD. The independent auditor still has one expected-count bug: v38 contains no `input_released` event row (count 0), but the check treats the absent dictionary key as `None`, not zero. No other auditor errors were emitted. Preserve both results unchanged; no retry.

## H / T / D / C / U

- **H:** Transferable time-weighted useful-control coverage remains unidentified without identity-bound physical down/up intervals, same-clock independently useful effects, and a compatible denominator in every domain.
- **T:** New allocation T0-02 reuses the T0-01 classifier with a frozen output-count normalization wrapper and a separately authored raw-only auditor. Six construction tests pass. Candidate ran once (exit 0); auditor ran once (exit 1); retries 0. Host-only deterministic source replay; no Docker/WSL/model/game/GUI/input/GPU.
- **D:** Candidate status is `HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED`. The auditor independently reconstructs v38/v39/OpenTTD event maps, correct v38 score count=1, DOOM analysis/raw hash joins, OpenTTD 7 down/0 up/7 neutral-terminal joins, 263 observer rows, 2 states and transition [91]. It rejects because `input_released` is absent in v38's sparse event-count map and code compares `None` to expected 0. All candidate/raw count-consistency checks otherwise emit no error.
- **C:** Frozen current-main SHA `f9633921c93530054b0d7320b1665df114050d52`; six input Git blobs at `279ee4aee96c5646360239409931821726566aa2` match current main. T0-01's candidate source and freeze are hash-bound as predecessor dependencies and unchanged.
- **U:** No physical held duration, useful-feedback latency, matched recovery benefit, safety, human tempo, task completion, or MAP01 exit is established. This failed audit is not a scientific refutation.

## Immutable artifacts

Allocation: `R133-CROSSDOMAIN-TIME-COVERAGE-59-T0-20261002-02`. Frozen source, inputs, candidate and auditor output remain in this directory. The next step is a distinct audit-only successor using this exact candidate result, with sparse event maps interpreted as zero only for explicitly absent event types and tests for that case. T0-01 and T0-02 will not be edited or rerun.
