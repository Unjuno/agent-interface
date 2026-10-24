# S20 result — saturated relay cancel reaches the Fake X caller before stdout resumes

**PASS_SCOPED (12/12 independent audit checks).** One fresh WSLc 3.0.3.0 session on current main `7b9383077f8f98873eab5eac70b13005c8d2138f` ran the exact standard public relay/caller test under CPython 3.12.14. The container had no network; the six critical source blobs matched current main; all 31 offline wheels matched their pinned manifest. The single unittest passed in 1.861 s (runner measured 2.383 s).

The relay had 16 ordinary responses queued behind a blocked stdout write. The public cancel was dispatched to the standard caller while stdout remained blocked. The synthetic owner readback recorded the key-up and an empty key/button set before the cancel returned; that readback preceded stdout resume by 114.244 ms. The cancel returned 115.290 ms after admission. The response itself was written after stdout resumed, as expected. The caller still reported `cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, `replay_allowed=false`, and `late_server_request_possible=true`.

The exact container, digest-pinned image, and unique session were deleted/terminated. The isolated 213,909,504-byte session VHDX remains at the unique path in `STORAGE-CLEANUP-STATUS.json`, with a retained SHA-256. S19's earlier pre-test lock-path failure remains a separate setup failure and is not pooled or rewritten.

This is a WSLc synthetic Fake X composition result. The release/readback is injected test behavior; it does not prove physical X/OS input release, a real GUI or application effect, MAP01, task success, efficiency, or reliability. The corresponding Windows CPython R01 already exists; S20 adds a WSLc platform-transfer sample only.

