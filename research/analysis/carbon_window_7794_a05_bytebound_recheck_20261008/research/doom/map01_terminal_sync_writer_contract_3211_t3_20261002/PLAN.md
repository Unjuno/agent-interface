# MAP01 terminal trace writer contract — T3

Status: FROZEN before candidate execution. Host-only synthetic child; no MAP01 allocation.

## H / T / D / C / U

- **H:** A newline-delimited JSON writer contract can preserve each synthetic session event as one physical JSONL record, including values containing embedded newlines, while the historical literal `\\n` delimiter fails ordinary JSONL parsing.
- **T:** At the current-main freeze, run one synthetic Python child that emits a fixed `probe` event (with embedded newline text) and one `terminal` event. In the same one-shot candidate, serialize that exact event sequence through a byte-for-byte historical delimiter control and a corrected additive writer. Retain both raw streams. Run a separate auditor that checks event equality/order, physical record count, hashes, strict JSONL decoding of the corrected stream, and rejection of the control stream.
- **D:** `PASS_WRITER_CONTRACT_SCOPED` only if the child exits 0, both streams reconstruct the exact two events, the fixed stream has exactly two physical lines and strict line-by-line JSON parsing succeeds, the legacy control has one physical line and fails the same parser, and all raw hashes/byte counts match. Otherwise preserve FAIL/STOP; no retry.
- **C:** Synthetic serialization contract only. Does not exercise the MAP01 session lifecycle, prove the original recovery terminal was emitted, or explain the #3202/#3211 timeout. This must not be described as a fix to the frozen runner or a formal recovery preflight.
- **U:** No MAP01/game/model/GUI/input, Docker/OrbStack, workflow dispatch, formal allocation, or timeout tuning. No retries. The legacy T2 result and all predecessor artifacts stay unchanged.

## Freeze and collision checks

- Repository: `Unjuno/agent-interface`; main at freeze: `73235730af05375fddf3a9d102d30632e7d43af5` (confirmed by `git ls-remote` and GitHub file read).
- Relevant main source: `research/doom/map01_recovery_cover_matched_v2_runner_3211_diagnostic_v2.py`; `JsonSession` Git blob `f5caf71a743a563b7de046b82d44db7ebe49e829`. GitHub main readback confirms its writer uses `trace.write(json.dumps(row, sort_keys=True) + "\\n")` (literal backslash+n).
- Prior T1/T2 findings are recorded on main via PRs #5984 and #5989. No existing branch matched `map01-terminal-sync-writer-contract`; this is a distinct additive contract test, not another timeout reproduction.
- New namespace: `research/doom/map01_terminal_sync_writer_contract_3211_t3_20261002/`.
- Runtime planned: CPython host synthetic child. Candidate invocations 1; independent auditor invocations 1; retries 0.

## Frozen implementation hashes

- `trace_writer.py`: `057EA56213623D1DE65D3DC7E9D4859D2BFDB58DDA9CE203AE75A3E64C9F0AC3`
- `candidate.py`: `CB68CE8B610362F8E1E298649192F85C4D86BC77AE3F9F812F8F025C3338D4FC`
- `audit.py`: `85C16DA623324E70B4E0A7990D37ED7D60C58CCD0CECAE817E4A1C98CD118264`
- `test_construction.py`: `06065A296C3BF1A24DF6CA81A51C697660845B5066990A1ABCEFE703BD9486F9`
- The freeze manifest will additionally bind this plan's final SHA-256. The candidate and auditor must verify all listed files before accepting the result.

Do not change any frozen file after the manifest is created.
