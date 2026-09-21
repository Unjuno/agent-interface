# Publication note — Issue #3986

This note is **post-measurement publication metadata**. It does not modify or retroactively replace the local preregistration, freeze, formal result, raw evidence, or independent audit.

## Chronology

1. The allocation `local-gap-clock-20260922-01` was preregistered and source-frozen locally against intake main `b2457b746a6df06f6536585dfe2ab937aff639f4`.
2. One 72-case formal invocation ran locally in the provided Linux container. Reruns/replacements/tuning were zero.
3. The original session could read GitHub but did not expose a write-capable route. The frozen evidence therefore records `github_issue_created=false` and the delivery stop `BLOCKED_TOOL_WRITE_UNAVAILABLE`.
4. A later session re-read current main, README, CURRENT_GOAL, ROADMAP, recent open/closed Issues, PRs and branches; targeted collision searches found no duplicate elapsed-time successor.
5. GitHub write capability was then available. Successor Issue #3986 and branch `research/gap-elapsed-clock-926-20260922` were created **after** the formal result. No text in the frozen evidence is rewritten to claim otherwise.

## Exact evidence carrier

The locally validated binary-capable addition-only patch is stored as two exact text fragments because the connector's large-file read surface is bounded.

| Item | Value |
|---|---|
| original patch bytes | 2,025,006 |
| original patch SHA-256 | `3eebe00328aab0f7d6abfb1ab6c6f41b0795abdc09de2d92e2185a4fd8b4fb75` |
| additive files in patch | 450 |
| local empty-directory byte-match | 450/450 |
| modified/deleted pre-existing files | 0 / 0 |
| part01 lines | 1–14,993 |
| part01 bytes | 1,336,755 |
| part01 SHA-256 | `17cc984caf42ea14164a051f84ea7711c2a679f310e26757643dad357c88e534` |
| part01 Git blob | `0b712b362c306ffcb3e4ced42cd0dc7167aa31ab` |
| part02 lines | 14,994–24,200 |
| part02 bytes | 688,251 |
| part02 SHA-256 | `9ebb502ed7f8f904487fcb12903e2f3bff962a74ffa337d4afd297a880dbbf4c` |
| part02 Git blob | `339f2a20284525e04aa7cb01a734c38101df19d0` |
| complete local ZIP bytes | 582,854 |
| complete local ZIP SHA-256 | `a96d896c96b8f605112cec97e61d13caf26875fdd2d593ecb1273fdc229f3974` |

The two Git blob IDs above were checked after upload against independently computed Git blob IDs from the original local patch split at line 14,993. Both matched exactly.

Reconstruct the carrier:

```bash
cat publication/original_addition_only.patch.part01 \
    publication/original_addition_only.patch.part02 > /tmp/gap_elapsed_clock_v1.patch
sha256sum /tmp/gap_elapsed_clock_v1.patch
# expected: 3eebe00328aab0f7d6abfb1ab6c6f41b0795abdc09de2d92e2185a4fd8b4fb75
```

The patch contains the complete retained additive snapshot, including raw per-case JSONL, SQLite database bytes via Git binary patch, source, audit and manifests. The original local delivery validation was against an empty directory, not a live main checkout; do not silently upgrade that validation claim.

## Direct review surface

For ordinary code review, selected files are also expanded directly beside this note:

- `PREREGISTRATION.md`
- `FREEZE.json`
- `RESULT.md`
- `RESULT_SUMMARY.json`
- `audit.py`
- `formal_controls.json`
- `gap_policy.py`
- `run_study.py`
- `worker.py`
- `schedule.json`

These are convenience duplicates of files carried by the patch. Apply the reconstructed patch to a checkout where this study path is absent, not on top of these already-expanded duplicates.

## Scope

Retained decision: `PASS_LOCAL_CLOCK_BOUNDARY_SCOPED`.

This is a notification-contract result only. It does not select 80 ms as a production default, create a timer wakeup, prove a delivery deadline, execute resync, establish model viewing/useful feedback, or close #3876 / #57 / #2789 / the broad ROADMAP.
