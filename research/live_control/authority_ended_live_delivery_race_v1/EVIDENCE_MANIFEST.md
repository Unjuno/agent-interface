# Evidence manifest — live authority-ended delivery-race v1

## Retained namespace

The branch retains:

- `REPORT.md`
- `prereg.json`
- `runner.py`
- exact executed `authority_ended_bridge_v1.py`
- exact executed `two_dispatch_gate_v1.py`
- `formal-result.json`
- `timing.json`
- `audit_retained.py`
- `formal-raw-text.json.gz.b64`

The `*_executed.py` duplicates are publication aliases of the same bridge/gate bytes and are not separate mechanisms.

## Frozen local identities

```text
52a07c66d8272cf93631f685c1a73ce425231258b0405ca1eee600f2ed429ded  prereg.json
63fcb603f8c8c841c2546e20e28f86acb0c7f243cf898156d856521f7bf9c362  run_live_authority_race_v1.py
2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e  authority_ended_bridge_v1.py
dc179545ced6790c55b348d6553047188eed83cbb2129cb576a83fa406dc1c87  two_dispatch_gate_v1.py
0d5052bbf485589e6231b44cf71963c668bf25de34550d2e171d426354b00d93  formal-result.json
4e8362b6f1799e43e5bc239bb5fa039012548add3b422f0b252870e03bc852aa  audit_live_authority_race_v1.py
90e3a4f8fcac101737451d1ad8037f5abe901ce98e4603ae7dde35311be2c135  audit_retained.py
0efbaa28bd195cfbbb0d888db9579890770b0a6cc67d7132143e9f698f87c390  timing.json
```

Published filenames `runner.py` and `audit_retained.py` are the reconstruction path; Git blob SHA is a separate identity namespace from the local SHA-256 values above.

## Raw text bundle

The deterministic uncompressed bundle is:

```text
a03c8a6818ddb27ef03f0b3521c8dfd73cd314b2580ab830993ec2425eabad92  formal-raw-text.json
```

The retained base64/gzip file is:

```text
4d5d7169e5e7c81d690554bb24ab1e8d269ccea70417aa62bcc8774aba528515  formal-raw-text.json.gz.b64   (SHA-256)
944e048a7b426797eb061f93a8e252a9530a5cfc  formal-raw-text.json.gz.b64   (Git blob SHA-1)
```

The GitHub branch tree was read back after upload; its blob SHA for `formal-raw-text.json.gz.b64` is exactly `944e048a7b426797eb061f93a8e252a9530a5cfc`, matching the Git blob SHA computed from the local frozen bytes. Therefore the retained bundle is byte-identical to the local source bundle.

`audit_retained.py` decodes this file, verifies the uncompressed bundle hash, verifies every embedded raw file against its own SHA-256, and then replays the race/release/admission/scorer assertions.

## Original raw source hashes embedded in the bundle

```text
01a609f9af79c953ed2db7512f55fb311db78970f3da1d372d851d017c53f520  events.jsonl
48b4ff296b4509ec4ea770b7a697e6cdbfc249ef97b0b7243418b4dfb790e2bf  owner-events.json
ada892eb4186ba4bdecb4f8bd53a83f9f09be81645f452a3f4767b47df24cce2  score.json
6ffae2e107eeef66eb21a8c2c20d0f117fd3d923db77fdbbea801f1ef69c90c6  scorer-samples.jsonl
e5976f533c0478d378961a283a12466431b351a30b0e3f6deef5f482ec11d216  scorer-summary.json
9db3ded8d1ebbe0076cdc0c21456193bc1c864871eb1ac9ef80efd90d4677e41  environment.json
01f35ffcc32595145dea3da60ac2d52030199413a981af69080130198b439d76  sources.json
7ce8447d3b0e649d05a21466f31002d1e093c50168f72d6bfa46076149f48943  harness-stderr.txt
```

PNG/AIT/setup-screen binaries remain local-only and are not needed for the ordering/release/admission/scorer claims.
