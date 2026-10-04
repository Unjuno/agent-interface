# v3 release backend → direct retained-input analyzer identity conformance — I84

**Disposition: `PASS_PRODUCER_CONSUMER_IDENTITY_ALIGNMENT` for the eight synthetic identity cases; live MAP01 telemetry remains gated.**

## H / T / D / C / U

**H.** The v3 per-key release backend should mark a release verified only for a matching non-empty string intent token; the direct retained-input analyzer should report ready only for that valid producer receipt, while malformed or mismatched identities remain not ready.

**T.** Freeze the v3 backend and fake-owner test fixture from PR #7352 head `b37a57eba77b120176e6f9c4f065da9aac353145`, the direct analyzer from PR #7356 head `17fb65363d5dcd21f58ed71e6e48b640ead391d8`, an eight-case identity matrix, and local WSLc image digest `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`. Run one CPU-only container with networking disabled and a read-only evidence mount.

**D.** Pass if the matching non-empty string control yields both a verified producer receipt and a ready one-hold analyzer result, and every empty, non-string, null, absent, or mismatched token case yields an unverified receipt and a not-ready analyzer result.

**C.** The backend's owner and executor are deterministic fakes from its committed unit-test fixture; this checks composition and schema agreement, not a live owner, X11, MAP01 or task effect.

**U.** Producer wiring and scorer behavior in a full v40 session, actual physical key release, useful-feedback onset, and bounded-recovery benefit remain untested here.

## Result

All eight cases matched the preregistered rule: the nonempty string positive control produced `owner_transition_verified=true`, `measurement_ready=true` and one hold; empty string, integer, boolean, explicit null, absent token, mismatched strings and a missing release receipt token all produced an unverified release and a not-ready consumer result. The independent raw-only auditor reports `PASS_PRODUCER_CONSUMER_IDENTITY_ALIGNMENT` with zero errors.

Runtime evidence from the sole WSLc container: Python 3.12.15 on Linux 6.18.40.1; UID 501; `cpu.max=100000 100000` and `memory.max=536870912`; `/src` mount options include `ro`; configured network mode `none`; no GPU requested. WSLc warned that swap-limit capabilities are unavailable, so swap was not bounded. The memory and CPU cgroup files confirm their configured limits; no claim is made about swap enforcement.

No live owner, X11, game, input dispatch, model, useful-feedback onset, recovery-benefit or formal allocation was run.
