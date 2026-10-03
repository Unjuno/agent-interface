# G23 model-assisted OCR repair

Status: `STOP_CLI_PROMPT_NOT_DELIVERED`

This package evaluates one requested model response on four in-sample OCR-abstained calculator cells from the G20 development corpus. The decision rules and exact inputs are in [`FREEZE.md`](FREEZE.md). The oracle remains host-only under ignored `private/`.

The one frozen CLI invocation exited 1 before inference with `No prompt provided via stdin.` It produced no stdout and no assistant final response. The raw stdout, stderr, and local receipt are retained under ignored `private/`; [`RESULT.json`](RESULT.json) contains only the allowlisted diagnostic and hashes. The independent local audit passed its receipt checks, but the candidate experiment is STOP, not a model result. No retry was made. This finding supports no recognition, accuracy, or desktop-control claim.
