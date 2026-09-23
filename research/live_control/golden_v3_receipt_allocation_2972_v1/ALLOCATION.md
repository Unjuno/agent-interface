# Golden-v3 receipt allocation #2972

Allocation: `golden-v3-receipt-allocation-20260920-a1`
Repository source: `main` at the source files fetched immediately before allocation.
Docker image: `agent-interface-2972:20260920`
Docker image digest: `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`
Network: `none`
Command:
```
docker run --rm --network none -v /tmp/agent-interface-2972:/repo:ro -v /tmp/lo2972-results-a1:/out agent-interface-2972:20260920 research/integration/golden_v3_second_domain_2246_v1/formal_matrix_runner.py --out /out/allocation-a1
```

Observed allocation:
- fixed eight rows completed; Xvfb and GTK fixture started
- useful: application effect receipt `{"saved":true,"text":"useful"}`, raw input ledger, X11 dispatch, verified release
- no_effect: accepted dispatch and no independent effect
- partial: application receipt with collateral field
- stale_repair: stale observation refused with zero backend emissions
- cleanup_failure: effect receipt plus cleanup failure retained; not task success
- unavailable/guarded/ambiguous: fail-closed pre-registered delivery refusals with no replay

Runner summary:
- `scorer_matches=true`
- `formal_receipt_order_ok=true`
- all eight independent gate rows classified
- the runner does not independently execute target/window replacement or source-identity mismatch; those remain unverified
- broad decision: `HOLD_FIXTURE_OR_CONTRACT_ONLY`, not formal #2606 acceptance

Image/source SHA-256:
- Dockerfile: `04eab4934e2f31ae555bd66260b3c61910cf9f12f78e5fd44ae1192d2d96bb42`
- formal_matrix_runner.py: `efcc7ce170010a7d8620ec512a4640cf81bcf38f0db24919f0291dfb048b7877`
- gtk_fixture_app.py: `a89740107f5b544cde8a0ab1ae9f1af1764498889f85c982d106301577685f4a`
- matrix_gate.py: `acda9418e4ef97698f43b4f3509d9fc1f671643098cf340182c9b81bdc6ffed3`
- golden_v3.py: `2e81a25f799318cccab971818ef3b5a8015eea937fda12445c1379df3842aae7`
- api.py: `e814ad5afa7590ef2db20f8a490144218b2e00e38dd43d2f153cf5503abab72b`
- contract.py: `268cf282c02f9e2dd38a8c45a36378049443ef2a2431063359011d0552b9c37c`
- selector.py: `e768be42677984830a4d9a8a5e5223fcb44b76d413ba8edd9f28acde7e3346ad`
- x11 backend: `c23cf5e87124cbaa2bc834f17cc5e3f9816d6ea38d54c772baf5c09613c813ca`
- x11 session: `70ffb0167a70efcf629221c8236dd19ba9fbc2ff3ffc18454f13a0f656b86a93`

This record preserves the actual Docker result and its limitations; no synthetic row is upgraded to a general integration PASS.
