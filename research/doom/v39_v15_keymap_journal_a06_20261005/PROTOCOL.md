# A06 protocol

Frozen before execution under Issue #59 comment 5986764896. Run one candidate invocation and one raw-only auditor invocation. No candidate retries or code repair after run.

The candidate uses a shared in-memory FakeX server bitmap, production release-batch backend v1 and owner v4/v3/v12/v10 source snapshots. A read-only sampler is called only after the backend's owner `input_state` call returns. A one-shot fault suppresses exactly the requested key's first KeyRelease server-state mutation; the owner's later terminal cleanup is not suppressed.

After each completed case the candidate appends its trace, release rows, owner records, and pre/post-cleanup keymaps to `run/cases.jsonl`. If a case raises, it appends the partial trace and rows to `run/failures.jsonl` before stopping. Final JSON stdout is supplemental; journals are primary run evidence.

The audit reads only the frozen candidate, source snapshot identities, final stdout/stderr/exit status, and case/failure journals. It does not rerun the candidate or reconstruct missing events.
