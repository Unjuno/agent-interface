 #3085 runtime GTK receipt matrix allocation
Date: 2026-09-20 Asia/Tokyo
Image: agent-interface-2994:20260920; digest sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c
Network: disabled; fresh container; working directory /workspace.
Command: python3 /workspace/research/integration/golden_v3_second_domain_2246_v1/formal_matrix_runner.py --out /out/run
Source hashes: formal_matrix_runner.py efcc7ce170010a7d8620ec512a4640cf81bcf38f0db24919f0291dfb048b7877; matrix_gate.py acda9418e4ef97698f43b4f3509d9fc1f671643098cf340182c9b81bdc6ffed3
Result hash: summary.json 656137bbd6227a70d3110119f3fac6f0d7531737bde57ed6223d3dce1cebc660
Result: PASS_RUNTIME_GTK_RECEIPT_MATRIX_SCOPED. actual dispositions exactly matched expected for 8/8 cases; independent gate classified all 8; useful/partial effects and release evidence retained; no-effect, stale, ambiguous, cleanup-failure remained non-success paths. Model/network calls 0/0.
Boundary: scoped GTK/X11 receipt-emission preflight; not full #2606 acceptance, model quality, broad GUI, or product readiness.
