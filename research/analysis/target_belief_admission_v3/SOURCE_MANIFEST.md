# Issue #4150 ID003 source freeze

Allocation: `target-belief-admission-4150-20260927-03`.
Base `main`: `91b5143989403754b360738c445f72b68b673718`.
This is a fresh publication/allocation identity after ID001 setup STOP and ID002 source-integrity STOP. Scientific constants, 8 profiles, 4 provenance states, 2 probe states, independent oracle, candidate/comparator, and decision gates are unchanged from the verified ID001 capsule. The only source-code change is the allocation literal in `experiment.py`; PLAN and SCHEDULE identify ID003.

## Frozen SHA-256

| File | SHA-256 |
|---|---|
| `PLAN.md` | `126bee4f342b1a4f43e0d0f5cbd8d3e0193168e9fab0ceff59f8dd7be0d50809` |
| `experiment.py` | `3d117395dba99ec483b7df36b06dc9e9483c8b2881a83f38a1f6a7668c173314` |
| `audit.py` | `47ed66b5b5d3ae0d08453fe5f084b554e5f8311b35b16694a62079666898a9dd` |
| `controls.py` | `e16c585ddd508cb85c1f49a07059306a8b564dbabcb166991d05ffe2b9a1eee6` |
| `test_contract.py` | `60436833f13b78d91fb8c99025b0f8673d56ea81d15fe5d4ee661c3444e4aea6` |
| `ENVIRONMENT.json` | `5d232537c06436f8eeef17fbe9e0c37f1ee1f37a18cf8206402aeedaf3fb7eb6` |
| `SCHEDULE.json` | `7db236c364cf56bdc964116a293aa50edb560537cd4604e657d122363789a03c` |
| `CONSTRUCTION.md` | `76b44e7eebf9684b6ed843300a8c62aa9a340d2193b9fa0354cc10f17a52d1fe` |

## Container freeze

OrbStack Docker, `python:3.12-slim` image ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, explicitly run as `linux/amd64`; `uname -m` returned `x86_64`, Python `3.12.14`. Network disabled; source mounted read-only; outputs go to a fresh allocation directory. Formal invocation limit 1, reruns/replacements/tuning 0.
