# T6 immutable artifact audit addendum

This addendum supersedes the earlier `STOP_UNCLASSIFIED_ORCHESTRATOR_EXIT` wording in `REPORT.md` without changing or rerunning the consumed allocation.

## Independently retrieved artifact

- Actions run: `36789533128`; artifact: `11131141471` (`map01-attack-start-gate-t6-36789533128`).
- Artifact ZIP: 85,236,522 bytes; SHA-256 `535b94ffeb7bc14d394f9f20e8baa5bc9b9f379b636c21c59db5444fa8d030f4` is recorded by the issue's prior independent ZIP audit. The CLI downloaded and extracted this artifact, but did not leave the original compressed artifact ZIP for an independent local hash check.
- Offline runtime ZIP: 80,117,931 bytes; SHA-256 `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`.
- Artifact verifier reports source manifest 2,592/2,592 files and all 12 wheels verified; the recorded Linux/amd64 image ID is `sha256:0c4393f9d2b7eab61335408338cc1df8de59f2661c49f435e727b927685f9868`.
- Frozen main and live main at execution both equal `33c19225f117d6d927a98e791e620de37479a927`.

## Retained outcome

`OBSTAC_EXECUTION.json` records exactly one candidate invocation, candidate exit 1, retry budget 0, and independent auditor invocations 0. `candidate-container.log` shows `PermissionError: [Errno 13] Permission denied: '/out/xvfb.stdout.log'` while opening the Xvfb log file. The failure occurs before `subprocess.Popen` starts Xvfb; therefore DoomGame startup, ready, initial observation, and gameplay were not reached. The frozen protocol correctly skipped the auditor because the candidate did not exit 0.

Disposition: `STOP_CANDIDATE_OUTPUT_MOUNT_PERMISSION_DENIED_BEFORE_XVFB`. This is an infrastructure/output-mount stop, not a startup-gate PASS or a scientific FAIL. Preserve the immutable artifact and do not rerun this allocation. Any mount-permission investigation or new candidate requires a fresh allocation identity and freeze.

This addendum is a direct readback of the uploaded execution evidence. It is not an independent raw-only scientific audit (the preregistered auditor did not run), and it makes no claim beyond classifying the pre-Xvfb stop.
