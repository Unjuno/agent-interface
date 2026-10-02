# T0-01 execution record

- Allocation: `LEASE-CANCEL-ACK-CONTRACT-HOST-T0-20261002-01`.
- Frozen base: `4cf0a3dfde1219671b671bf0a9079a11dcb2e159`.
- Frozen Lease Git blob: `b9dac6bb4063928354733d79bf371909a288a3d1`; SHA-256 `e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f`.
- Candidate: `python -B candidate.py --out results/host-t0-01/raw.jsonl`, invoked once, exit 0, 12 rows.
- Auditor: `python -B audit_raw.py results/host-t0-01/raw.jsonl results/host-t0-01/audit.json`, invoked once, exit 1, `FAIL_LEASE_CANCEL_ACK_CONTRACT`.
- Candidate/auditor retries: 0/0.
- Raw SHA-256: `0cf901c50d59ebe4a2bf0365f71927c541f518f31584498ae758519c08cb218a`.
- Audit SHA-256: `dac36ec8c2a2e5a524517c659bc3ae7b0cd7c76036ed22ac77b0aefe2744df20`.
- Cause: candidate did not advance fake clock to deadline in the no-cancel case; actual Lease returned `False`, candidate continued, independent audit rejected the declared deadline scenario.
- Scope: host CPython; exact frozen Lease class; synthetic clock; no Docker, GUI, model, GPU, external input or action.
- Disposition: preserve as harness failure; no repairs/retries within this allocation.
