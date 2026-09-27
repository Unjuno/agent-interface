# Postcondition strength: bytes are not the whole Git entry

Decision: RETAIN scoped `full_entry` prepublication postcondition. Issue #410.

## Question
After read/write/scope/ancestry/CAS gates pass, is exact target byte content enough, or must a requested postcondition also bind entry type/mode?

## Frozen comparison
Publication base `0dd239b7db10831a4e8ac078d3a32d4be6370e3d`; premeasurement GitHub freeze `b4e207d7d4c6f7355f91d0b70d3692eb4f142502`. 56 fresh bare Git repositories: 2 policies x 7 scenarios x 4 repetitions. No measured ID rerun.

`bytes_only` checks exact requested bytes at `output/effect.txt`. `full_entry` adds mode `100644` and object kind `blob`. All other read/write preconditions, changed-path scope, current ancestry and final current-OID CAS are identical.

## Results

| Scenario | bytes-only correct | full-entry correct |
|---|---:|---:|
| correct | 4/4 | 4/4 |
| unrelated state preserved | 4/4 | 4/4 |
| wrong bytes | 4/4 reject | 4/4 reject |
| wrong mode | **0/4; applied 4/4** | **4/4 reject** |
| wrong kind/symlink | **0/4; applied 4/4** | **4/4 reject** |
| write conflict | 4/4 reject | 4/4 reject |
| ref race after validation | 4/4 reject | 4/4 reject |
| **Total** | **20/28** | **28/28** |

The bytes-only control therefore committed 8 authored malformed entries whose byte payload matched the requested payload. A byte postcondition is not equivalent to a typed entry postcondition.

## Verification
Independent extraction reproduces all 56 audit rows; 7 tests pass; 1,067 manifest entries match with zero hash mismatches. Raw evidence archive is conversation-only: 90,116 bytes, SHA-256 `e17cccbe65266f9ebad27716df78655d03251a7c90edf55a164cc92571eb5432`.

## Scope
This is a generated local Git fixture. Required content/type/mode is authored and may itself be wrong. Refusal means the authoritative target ref was not moved; candidate objects were still created for inspection. No GUI/model/Doom/network/user data, performance, automatic semantics or production claim.
