# A04 source audit follow-up on current main

This read-only check does not rerun the candidate or audit. It supplements the
retained first-outcome record because the package cannot currently reproduce
that outcome from its published files.

`shasum -a 256 -c SHA256SUMS.source` reports three mismatches:

| File | Recorded SHA-256 | Current file SHA-256 | Syntax check |
| --- | --- | --- | --- |
| `candidate.py` | `c403b4750b4eaccfbc2d97b2b38dbe77611fac4e3460a0d410576ed97e44abd3` | `4ed72f7bf3f37c4ac00861de09ee7d569954488ed8a0994fda92a258cb00643f` | FAIL: unterminated string at line 102 |
| `audit.py` | `8c426b37f9e8723ec1b715610a6f914e37a0f8951a5e9c2076f5c8b09ef20080` | `69a21440bdb28d73cf764006350381b1222e5d458bb93fd547c0f220d17811a1` | FAIL: unterminated string at line 59 |
| `controls.py` | `8affc6ade63f04546ab02d910e41e35eb0be689e26373b6541c80c14f47fb59f` | `b34363fd8f45e6629b9fb17cfafc2d50af7a88d35e06ae84250f36e6907f04e6` | PASS |

`audit_cli_repaired.py` remains a separate syntax-valid CLI copy only; it does
not repair the candidate, reconcile the three source identities, or replace the
missing 2,925,419-byte formal raw. The recorded A04 first-outcome label is
therefore retained as historical testimony, not independently reproduced
evidence. The separate six-case T0 result remains unqualified. No source,
result, or predecessor package was rewritten.
