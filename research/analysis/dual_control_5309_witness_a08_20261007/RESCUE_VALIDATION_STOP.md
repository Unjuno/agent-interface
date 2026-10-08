# Rescue-validation STOP: container-only auditor entry point

During current-main rescue validation on 2026-10-08, a local `auditor.py --help` probe was mistakenly invoked. The script has no help-only argument path: it entered its normal entry point and stopped immediately while trying to read `/input/candidate-input.json`, which is available only in the pinned container mount layout.

No candidate process was invoked, no auditor reconstruction completed, and no retry was made. This is a rescue-host tooling STOP, not a change to or replacement for the frozen A08 result. The original raw and audit files remain byte-for-byte unchanged. Do not run the A08 auditor or candidate again; any further execution requires a separately authorized, newly allocated successor.
