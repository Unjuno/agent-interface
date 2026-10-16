# #3031 bounded activation allocation

- Date: 2026-09-20 Asia/Tokyo
- Image: mixed-formal-3025:20260920
- Digest: sha256:c8fec4d7541b306b9266ce8d7800abad8e665e63d6ea1e5f62574d4b122a28d1
- Network: disabled; fresh container allocation.
- Code change: bounded xdotool activation (3s), fallback focus, active polling; timeout converted to structured return.
- Outcome: FAIL_MIXED_APP_LONG_SESSION; exit 1; event_count 21; checks [true,true,false,true,false].
- Passed: focus drift refusal, modal transition/recovery, Chromium replacement identity.
- Failed: Calc geometry transition and return-to-earlier-Calc active validation. Raw activation events report BadWindow for Calc XID 6291457.
- Model/network calls: 0/0.
- Source hashes: formal_session.py f4b2b429dd3f49e57eb6641baf00ad272db375b8e509fb3d40be69c51954115a; Dockerfile 963f32721bcc1e7657dc13bfb6ebad173ccce89eb068f92f69a32d3f54651f44; capture_run.py eb19a0a5e6760698e4194806c8044fef1b36d2ae3203316d1f4b818d52b24782; RESULT.json d320d686acef7519fa35ad2af5f4f2521ec5ccebca748d2aaab803eec25600b0.
