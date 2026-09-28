# W2 lease authority v3 — contract-aligned terminal/closure boundary

This candidate is a successor to the retained lease-close matrix. It does not edit or replace the frozen W2 verifier, auditor, schema, fixture, candidate v1, or candidate v2 records.

## H / T / D / C / U

**H.** Under a complete, single-clock trace, input authority is bounded by the matching actuation's `LEASE_OPEN`/`LEASE_CLOSE` interval. `PROGRAM_TERMINAL` is a distinct program-lifecycle event and is not itself a lease closure. If terminal is intended to revoke authority, the trace must record a corresponding `LEASE_CLOSE`; absent/foreign close-actuation lineage is held rather than inferred.

**T.** Against the exact frozen eight-case W2 fixture (SHA-256 `6a693f06b1b4be15a8da35ec3aaf806d7fb3601091c8ef638c516069d1b4e95f`), version only the `release-before-terminal` open actuation to A4 and compare: a post-terminal edge with no close, an explicit close before the edge (even if earlier/later than terminal), a close after the edge, an edge/close interval overlap, and a same-lease close missing actuation lineage. Then exhaustively compare candidate, independent raw oracle, and the contract-derived lease interval rule over all edge intervals on integer endpoints 0..5, absent/valid/unknown/invalid close and terminal intervals, and four close-lineage relations. Run the new tests plus the existing binding/close suite.

**D.** PASS only if the five targeted controls produce the expected lease-boundary dispositions, candidate and raw oracle agree, the contract-derived rule has no mismatch across 48,384 combinations, and all 26 combined host tests pass. A terminal-only rejection is a policy mismatch; any oracle divergence is FAIL. Unknown/malformed close time and same-lease missing/foreign actuation lineage HOLD.

**C.** A system may intend terminal to revoke the running program's actuation even before a separate close is observed. The measurement contract models program terminal and lease authority separately, and the schema has a distinct `LEASE_CLOSE`; this test therefore does not infer implicit closure. Incomplete traces, lease TTLs, and external worker presence could change interpretation.

**U.** Python 3.12.10 Windows host CPU; synthetic fixture only. No Docker/formal allocation, runtime authority, GUI, model call, input emission, or task effect. Equivalence is finite-model scoped and does not prove implementation/backend behavior or the contract's completeness assumptions.

## Result

`PASS_FINITE_LEASE_AUTHORITY_POLICY_ONLY`: candidate/oracle and contract-derived rule agree over 48,384 finite combinations; the five focused boundary tests pass; the combined host suite passes 26/26. The post-terminal/no-close edge remains authorized under this explicit lease-only model, while a recorded same-actuation close before the edge rejects it. Candidate v2's terminal-as-authority-cap proposal is retained as an over-restrictive alternative, not adopted as the contract result.

## Reproduction

From this directory, with the frozen fixture at `../o2-w2-independent-audit-20260928/trace-cases.json`:

```powershell
python -m unittest -v test_lease_authority_v3.py test_binding.py test_binding_v2.py test_binding_gate_cli.py test_close_order_cli.py
python exhaustive_lease_authority_v3.py
```

Source pins, exact current-main W2 blob IDs, and scope are in `FREEZE_lease_authority_v3.json`; summary result is in `RESULT_lease_authority_v3.json`.
