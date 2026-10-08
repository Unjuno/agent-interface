# Evidence manifest — Inkscape authority-ended ABI v2

## Formal source identities

Frozen before formal seed 994600:

```text
37e6551baedaddad50ca8ef64677e3c387f742875ad3e28fa6ea630e58ad7d51  authority_ended_bridge_v2.py
dc98340c5434160684802a92f04d96f47420bf908198f8861b2148cbd12bdc72  post_authority_normalize_v2.py
408060fd7867c2ad8d4eb956b18804a998472c1d2b2c17bfedca43f40daf81ee  executor_v10_authority_ended_v2.py
8b04c9bfffd50ba0d5416977040d471962138559866558a87aeb5a3a20cd27b6  cause_servo_interactive_v7.py
4ab524fdb7f73b21e75313ef2f60ddcf6232bec0617a9b0d0a7480cb0cd229d7  cause_servo_socket_v9.py
3b46c686783c79e5087629921c920b385865c67e99c6e4648c24b8cae97f678f  run_live_v2.py
69d2b2975d5cd0911af2952085eb481f590468d47f5e73cc0256bd3714ae1541  post_release_observation_v2.py (unchanged base collector)
```

Pinned base files used by `build_candidate.py`:

```text
0eac224498d7b1dbe17a77ad05f39f6e66835120059928cb4f8c7faf731b6087  executor_v9.py
c0358690c3c4043c6e01776b04afc7b7ff8a3c9ece9b626c0799fd7219cbb5e6  cause_servo_interactive_v6.py
dc79236a74c253e4633ac6b92acc1776cb4b8db7853dce8e312786d7445988c2  cause_servo_socket_v8.py
```

The repository retains bridge v2, normalizer v2 and a deterministic build script that reconstructs the executor/interactive/socket candidate from those pinned base sources and verifies the expected candidate hashes.

## Formal result identities / retention boundary

```text
ddc16e6d9c9f4889a8d1694773120b79837111b227ddf2c6bc70b1476a64fd06  formal result.json
6ce0ae36eae0994e7cb99293e7324ccb8e3b7127be7bc39e8fd686400b552a58  formal audit.json
4090af1e9e050db119c09534af5cc31ce0f2ba2b635773318819813682496840  full offline 15-case result.json
```

`formal-evidence.json` retains the full terminal, interruption/release records, both post-release observation records, all admitted input events, bridge result, SVG result, timing/audit summary and hashes of the original raw text sources.

Original raw source hashes:

```text
e6f0eb32bce93ca972f008b06cc44b6ace57666e687b44d6df07d729bd700ee6  events.jsonl
18af0cf2ae32c0c7d090918ee1a76e69f8171858b2e8e40b7b33fe55841a71cc  owner-events.json
22abe085581621c28920f645411f78f1b2edfc0a2a483099bf999c26d71764d9  sources.json
47c889196f25b4b1c56cfe72c1658c00e3259fd34724142fb6024a289b625f16  shape.svg
```

The 11 PNG/AIT frame binaries remain in the disposable container and are not claimed retained on GitHub. The local independent audit verified all 11 transported AIT frames exactly equal their corresponding PNG pixels; this frame-level audit is reported with explicit local-only binary scope.

## Rejected construction candidate

`construction-failure-v1.json` retains the pre-live v1 representation defect: two actual captures were being represented as `captures=1`. It was rejected before formal live execution and is not silently overwritten by v2.
