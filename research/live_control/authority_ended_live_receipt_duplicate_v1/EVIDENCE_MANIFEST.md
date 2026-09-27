# Evidence manifest — live authority-ended duplicate receipt v1

## Executed source identities

The formal preregistration froze these local SHA-256 values before seed 994300 ran:

```text
2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e  authority_ended_bridge_v1.py
7a45327f419e9188fde3b506c5402fc8f454127336c60c90035a8baf0dca9382  replan_receipt_ledger_v1.py
96866eca4d61a821f41640627172f81840beeb8f35aa6d4523e2dd41f6dee94e  run_live_receipt_duplicate_v1.py
```

The retained bridge and ledger files are byte-identical to the executed local files. Their Git blob SHA-1 identities are respectively:

```text
9fcfdce5229cb58b3d1a17aacbcef0cb44bd10f1  authority_ended_bridge_v1.py
85ce5fb14767a35b28c5b6123393041aa1ae747c  replan_receipt_ledger_v1.py
```

`runner.py` is a reconstruction/publication copy of the formal harness, not byte-identical to the executed local runner. The exact executed runner remains identified by the frozen SHA-256 above and exists in the disposable experiment container. Do not substitute the published runner blob identity for the formal source identity.

The original full raw text files also remain local-only. `compact-evidence.json` retains the claim-relevant terminal/release/admission/scorer records plus SHA-256 identities of the original raw files. `audit_retained.py` audits the GitHub-retained claims without pretending the complete raw event stream is present.

## Original raw text SHA-256 identities

```text
96232e30fe21be9f118515fc2498ba7f419fc097d4515fcdfc48478390d0ce8c  events.jsonl
796bf184196954df6a4da04a602ca60f5a10a60cd2b50dff25d8d83b3bec2661  owner-events.json
1713ab2bf315674112571f4b6fd6f91b59f0e6372e5b0c1b349dd80a567a777b  score.json
66f18f2527416927e0b340e50f9e6c5167e9bdb76c082f5ed3147d9175abcd9e  scorer-samples.jsonl
3862ba5e130973dfbfe905fbd7da7015caa56c484aac4af5333e339f0ee42945  scorer-summary.json
0547a8234b4ef9c9f30a13c535f3d2ee59b37f1b37064066c4bfa27eaeb0f25c  environment.json
01f35ffcc32595145dea3da60ac2d52030199413a981af69080130198b439d76  sources.json
ee28d8e4bb3ca8c0b2f2f25ee79406b808dd0857e774a6e3fff05286cc2a287f  harness-stderr.txt
```

PNG/AIT visual binaries are local-only and are not required for the duplicate-receipt/release/input/scorer claims.
