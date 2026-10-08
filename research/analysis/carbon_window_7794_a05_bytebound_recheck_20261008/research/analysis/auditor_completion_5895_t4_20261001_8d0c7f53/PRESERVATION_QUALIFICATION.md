# Historical STOP preservation qualification (2026-10-02)

Retain T4 as `STOP_BEFORE_CANDIDATE / NOT_EVALUATED`. The published exit receipt is 125, stdout is empty, and stderr records Docker's invalid `rw` mount-field diagnostic. No target CLI case or independent auditor result is claimed.

Receipt completeness is limited: the committed stderr does not contain the shell-redirection diagnostic mentioned in STOP.md, and no `candidate.inspect.json` is present in the published package. The missing receipts-directory/CID details remain contemporaneous owner-reported observations, rather than facts independently established by the retained stderr. The original STOP and receipts remain unchanged.

README, PREP.json and START_GATE.md are historical preparation snapshots. Pending-start fields, future-facing launch instructions and the planned two-container sequence are not current authorization or evidence that those containers ran. This one-shot allocation is terminal and must not be retried.

T4's preparation pinned Linux/arm64. The [later Issue #5895 scope correction](https://github.com/Unjuno/agent-interface/issues/5895#issuecomment-5931146854) identifies the canonical Linux/amd64 requirement; T4's local “pinned platform passed” statement does not establish compliance with that canonical scope. No target experiment ran on either platform in this T4 record.

All original source, preparation, STOP and receipt bytes are preserved. This merge makes no scientific PASS, arbitrary-input auditor-safety or runtime claim, alters no predecessor including held PR #5899, and authorizes no launch, repair or rerun.
