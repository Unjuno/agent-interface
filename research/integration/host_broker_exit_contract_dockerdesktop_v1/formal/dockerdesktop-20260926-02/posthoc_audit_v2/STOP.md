# Posthoc audit V2 allocation 01 — STOP at CLI argument parsing

Classification: `STOP_AUDITOR_UNRECOGNIZED_ARGUMENT`.

The frozen audit container was created once on the pinned Docker Desktop image with network disabled and read-only study/runtime/raw-evidence mounts. Python's argument parser rejected the extra `--evidence /evidence` arguments before entering the auditor function; its exit code was 2 and no `posthoc_audit_v2.json` was produced. Therefore this attempt did not inspect or alter any raw formal evidence and provides no audit verdict. Its exact command, stdout, inspect and exit receipts are retained beside this note.

This audit attempt is consumed and is not rerun in this output directory. A separately frozen read-only audit V2B may differ only by omitting the unsupported option and using a new output path/container name; the auditor source, input evidence, decision rule and explicit host-exit HOLD remain unchanged. No formal case is rerun.
