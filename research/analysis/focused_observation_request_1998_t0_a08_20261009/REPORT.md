# A08 result: PASS_METHOD_SCOPED

The independent raw-only auditor passed all 27,664 frozen synthetic cases with zero errors. The candidate and auditor each ran once; retries were zero. The result is a finite request-contract finding for Issue #1998, not live computer-control evidence.

The matrix crossed 16 frame states (two epochs, two window identities, focused/unfocused, and two distractor states) with 1,728 requests per frame. It included frame-id/epoch/identity/focus-token mismatches, uncertain versus inferred reason, target/other/missing regions, unique/ambiguous/empty candidate sets, and declared/empty/out-of-bounds/wrong bounds, plus one full-frame control per frame.

The audit reconstructed 16 exact `FULL_FRAME` outputs, 16 valid exact focused crops, and 27,632 fail-closed refusals. All 16 focused evidence objects were strictly smaller than the full evidence object (92–97 canonical JSON bytes saved per case; 1,512 bytes total). The two distractor states preserve identical pixels in both declared regions while full frames differ. Action authority stayed false for all outputs. Six mutation controls (drop row, corrupt crop, corrupt full frame, grant action, alter frame hash, and accept stale request) each produced a new specific audit error.

The claim ceiling is deterministic synthetic standard-library semantics. This does not establish real OS focus detection, GUI correctness, model usability, task success, latency/token benefit, cross-domain transfer, runtime promotion, or product capability. The earlier A05/A06/A07 runner/auditor HOLDs remain unchanged.
