# Independent review qualification — 2026-10-03

## Current supported disposition

T0's retained records report `PASS_WSLc_DOCKERFILE_BUILD_RUN_SMOKE` for the one minimal cached-base build/run. T0A's literal first CLI output remains `PASS_T0_RECEIPT_AUDITED`, exit 0. **That CLI output does not establish the full declared T0A acceptance gate: `DECLARED_AUDIT_GATE_NOT_ESTABLISHED` / partial audit method gap.** These are separate layers, not a replacement or silent reclassification of either first output.

The read-only reviewer inspected PR #7020 at `d37044cb6a7f8fadcb6454607d8d52f6c0beb51d` against merge-base `3cdb84dc177f3efcfa4fb2fafc2eec87832515b5`. It verified all 17 local Git-blob identities against that GitHub head, all 16 manifest entries and both freeze tables, and agreement of the currently retained image IDs. It found two P2 validation gaps in the frozen auditor. No new runtime command or formal audit was run during review or this qualification.

## Findings verified against the frozen implementation

1. `audit_t0.py` checks byte counts/SHA-256 only for `Dockerfile`, `payload.txt`, and `probe.py`. It checks selected semantic fields in `build.output.txt`, `run.output.txt`, `POSTRUN_CHECK.json`, and `RUN.json`, but never enforces those four inputs' frozen byte counts/hashes. Thus the `AUDIT_FREEZE.md` D condition that all frozen-input hashes validate is not established by this CLI. A changed unchecked field or appended build text can leave its selected checks satisfied. The existing five tests do not cover this gap.
2. The auditor checks the build-output image and the `POSTRUN_CHECK.json` inventory image against a fixed constant. It does not check `RUN.json.build.result_image_id` or `RUN.json.postrun_check.image_id`; its output image ID is the constant. Therefore the original claim of a code-enforced comparison across build/run/inventory records is too broad. The current recorded values agree, as independently inspected, but mismatches in these unchecked fields would not be rejected by this implementation.

## Publication and scope decision

Preserve `audit_t0.py`, its tests, both original freezes, `AUDIT_RESULT.md`, all captured outputs/run records and original `MANIFEST.json` unchanged. Preserve the original result text as historical first interpretation; read it with this explicit qualification. No stronger audit implementation, formal retry, or application migration is delivered in this PR.

The narrow T0 capability evidence may be archived with these limitations. It proves neither runtime benefit nor complete compatibility; record consistency is not independent attestation of command execution, separate stdout/stderr, invocation times or counts. Any stronger auditor requires a separately versioned implementation and prospective validation, without replaying T0 or reusing T0A's allocation. Do not create an additional research Issue solely for this local validation repair.

`PUBLICATION_MANIFEST_V2.json` inventories the qualified current package. The original `MANIFEST.json` remains the 17-file publication snapshot at `d37044cb6a7f8fadcb6454607d8d52f6c0beb51d`; its README hash refers to the pre-qualification README at that exact head. The current README only appends a notice. Neither manifest attests that the frozen auditor enforced every listed hash.
