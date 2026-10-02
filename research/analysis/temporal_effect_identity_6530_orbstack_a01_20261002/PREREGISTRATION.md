# Issue #6530 OrbStack allocation A01 — temporal-effect identity

## H / T / D / C / U

- **H:** Under the frozen `America/New_York` 2026c rules, a typed effect oracle detects a planted wrong recurring instant that both display-string and offset-only comparators accept, while returning `AMBIGUOUS_UNRESOLVED` rather than choosing a fold when intent omits disambiguation.
- **T:** Run the already frozen eight-case deterministic fixture (ordinary time, both fold choices, unresolved fold, spring gap, wrong local recurrence, no save, duplicate) through one candidate container, then one separate raw-only auditor container. The independent UTC truth table is read-only to the candidate. No model, GUI, account, calendar, invitation, user data, or network.
- **D:** `METHOD_PASS_SCOPED` iff all eight classifications and independent UTC expectations match; the recurring-time planted error is rejected while both simpler baselines accept; unresolved fold lists both valid instants; and no-save/duplicate controls fail closed. Any mismatch is `FAIL_METHOD`; image/source/TZDB mismatch or infrastructure failure before candidate is `STOP/HOLD`, not a scientific result.
- **C:** Exact persisted-event comparison and documented application-specific rules may already suffice; this synthetic typed layer may add no useful discrimination beyond the recurrence control.
- **U:** One zone, rule release, and authored schema do not generalize to GUI applications, other zones, floating/all-day events, future TZDB changes, or user-intent ambiguity beyond the enumerated fold. No calendar or safety claim follows.

## Allocation boundary

Allocation: `TEMPORAL-EFFECT-IDENTITY-6530-ORBSTACK-A01-20261002`. This is a new OrbStack-runtime allocation after the predecessor's WSLc environment STOP. The predecessor remains immutable: formal candidate/auditor/container counts were 0/0/0. Do not invoke WSLc or mutate that run. This allocation uses the frozen source/fixture/truth from PR #6666 unchanged, but freezes the actual OrbStack engine, platform, image and TZDB identities in `FREEZE.json` before formal invocation. Candidate once; auditor once only if candidate exits 0; retries 0.

The preflight is environment inventory only: digest-pinned image inspection and reporting Python/TZDB/zonefile identities. It did not read the fixture or call candidate/auditor code. Construction tests ran on the host before this freeze and are not formal evidence.

Candidate container: `--pull=never --network=none --read-only --cpus=1 --memory=2g --memory-swap=2g`, source and fixture read-only, only candidate output writable. Auditor container has separate output, source/truth read-only, candidate raw read-only, and no network. The Docker VM cgroup reports CPU `200000 100000`, memory `4294967296`, swap `0`; Docker configuration is recorded separately from claims about enforcement.
