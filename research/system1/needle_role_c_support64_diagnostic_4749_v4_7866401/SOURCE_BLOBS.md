# Frozen executable source identities — Issue #4853

Git blob IDs below are read-back from GitHub for the exact frozen allocation source. The upstream runner is also independently anchored to the existing #4749 main path and matches blob ecd3a0414178f38535406573314793a40b353878 exactly.

- `source/upstream_runner.py`: `ecd3a0414178f38535406573314793a40b353878` (#4749 main runner)
- `source/paired.py`: `57f0999a6c98c324838fb95fdad56bc6d263e312`
- `source/prefix_contract.py`: `65313ceb9ff532b9f6c78b1cf6c33e294b6e816b`
- `source/construction_test.py`: `81a34387401d86154c64c581e27f8909169c3a58`
- `source/audit.py`: `e6f7b6db3f6a6aded60086783f5776b8e1af01be`

All five were fetched from the frozen allocation branch, added to this integration branch, and read back; blob IDs matched exactly. Git blob IDs are the canonical byte identities (including recorded line endings).
