# S18 result — target-generation mismatch refused before input

**PASS_FAKE_X_TARGET_GENERATION_REFUSAL_SCOPED.** One fresh WSLc 3.0.3.0 isolated session ran the exact current-main standard-caller test on CPython 3.12.14. Its one unittest passed (test-reported 2.846 s; runner measured 3.364 s). The pinned Python image was pulled once; the container had no network and mounted source, runner, and wheels read-only. All 31 dependency wheel hashes were checked before offline installation.

The standard caller observed and minted a target at generation `ad4a5888…d8be43f`; immediately before dispatch, the Fake X identity reader returned a different generation `f8481b03…4f5b78`. The public result was `refused`, with guard reason `process_generation_changed_or_missing` and `input_dispatched=false`. No accepted key press receipt exists. `task_success` remained null and replay stayed denied. The mismatch used a synthetic process-identity fixture (PIDs 123 and 124), not a real desktop target.

The independent post-run audit passed all 20 checks, including source identity, 13 raw-record hashes, exact-name preflight, and container/image/session cleanup. This advances target-generation rejection through the standard caller in WSLc. It does not test physical input, release/recovery, real app/MAP01 effect, matched efficiency, or reliability.

The isolated 288,358,400-byte session VHDX remains at the unique path recorded in `STORAGE-CLEANUP-STATUS.json`; the earlier command-policy rejection blocked deletion of these generated VHDX files, so cleanup was not retried.
