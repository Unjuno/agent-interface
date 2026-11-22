# Issue #57 ProspectiveRun synthetic lifecycle boundary R02

## Scope and setup
- Base source: current main `490d7bcb4d84927116112e5ff348cdeadfc489d6`; local candidate includes R01 test changes at `9933a5a2572eb49bde46c6f1c7cde88df9c272c9` plus uncommitted R01 packet/docs.
- Host/runtime: Windows CPython 3.13.14.
- Uses a fresh local TEMP evidence root and a deliberately synthetic allocation attestor. No provider, GUI, native input, Docker or WSL.
- Exercises four assigned plain-arm rows: nominal success-shaped outcome, provider failure with complete synthetic usage, deferred outcome, and completed outcome with UNKNOWN usage. No task custodian is supplied, and only four of eighteen assignments are recorded.

## Decision rule
PASS only if all four rows remain in lifecycle custody with their original caller envelopes, each remains HOLD (no eligible projected row), finish stays HOLD with the fourteen assignments identified as missing, and dispatch remains disabled. This is a boundary/negative-control experiment, not evidence that the live caller is integrated.

## Commands
Run the fixed inline harness twice normally and twice under `-O`, each with fresh evidence roots. Preserve separated stdout, stderr, exit codes, run manifest, journal and adjudication for each mode. Initial harness setup failures are retained and excluded from the passing reruns.
