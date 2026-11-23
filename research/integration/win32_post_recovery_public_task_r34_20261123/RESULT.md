# R34 result — same target generation remains fenced after recovery

**Disposition: STOP_CUSTODY_FENCE_TARGET_GENERATION_FENCED_BEFORE_INPUT.** The one-trial allocation is consumed; no retry was made.

On current main 87b5b459a56c636934947a2fc7616f26150e8b9a, the public source A dispatch became UNKNOWN with release unconfirmed, task success null, and replay denied. The separate public orphan recovery returned ecovered, confirmed release and neutral readback, and verified the 2 s late-input horizon over 77 samples. The delayed fixture  appeared as a factual effect after expiry; it is not attributed as eligible task success.

After fresh foreground confirmation and public observation, the follow-up used the exact same Win32 target generation as the recovered source (7b9e99cc…52dac). The public dispatch was rejected with CUSTODY_FENCE_TARGET_GENERATION_FENCED before operation invocation or input. The independent event log contains one A event and zero B events; state remains . The fixture and raw evidence are preserved, the durable custody fence is clear, and no task oracle success is claimed.

This establishes the current boundary: a fresh observation does not create a fresh native generation for the same window incarnation. A subsequent distinct task must use a genuinely new target generation (for example, a separately created fixture window). This packet does not establish that cross-target continuation succeeds, nor does it close #57's public caller task-success gate.

The original runner summary is preserved as aw/runner-cohort-summary.json; aw/cohort-summary.json is the adjudicated stop summary. All raw artifacts and source/condition hashes are retained.
