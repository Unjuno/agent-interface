# Issue #3637 — raw-only audit of #3626 formal-03

This successor independently re-adjudicates the merged #3626 formal-03 record without running GTK, XTest, MCP, or any input. It does not edit the predecessor's PASS, source, or raw bytes.

## H/T/D/C/U

- **H:** Counter-region pixels and a complete path/hash inventory can distinguish a rendered `COUNT 0`→`COUNT 1` effect from title metadata and incidental hover changes, while accounting for the eight raw captures not referenced by the original row record.
- **T:** Verify the immutable formal-03 input tree against a SHA-256 manifest captured at main commit `961f14b836e549ca5f6cfb6bf3ef4b470e91b1b5`; validate row/state references and `SHA256SUMS`; crop a fixed counter-label region from all positive and no-effect before/after X11 frames; produce a contact sheet and auditable hashes. No allocation or retry.
- **D:** `PASS_RAW_AUDIT_SCOPED` only if the input tree exactly matches the captured inventory, all linked artifact hashes/lengths validate, all positive counter crops show a distinct common post-state, all no-effect crops remain identical, and corruption controls are detected. Missing visual or file evidence yields the corresponding HOLD; a contradictory crop is FAIL.
- **C:** Same retained formal-03 rows and pinned frame dimensions. The positive/no-effect label ROI is compared independently of the button region, where pointer hover can change pixels.
- **U:** This is a post-hoc artifact audit only. It does not rerun GUI input, repair or rewrite #3626's historical decision, compare representation arms, establish usability/latency/token benefit, or close the host/model-visible #3370 gate.

## Reproduce

From the repository root, after installing the already-declared `research/requirements.txt` dependency. The committed frozen manifest already exists; do not run manifest capture as part of normal reproduction:

```bash
python research/experiments/issue_3637_formal03_raw_audit_v1/src/audit.py
python -m unittest discover -s research/experiments/issue_3637_formal03_raw_audit_v1/src -v
```

The `--capture-manifest` option is only for a one-time setup when deliberately creating a new manifest at a separate, nonexistent path; it refuses to overwrite an existing manifest. For example, use `--manifest /tmp/issue-3637-manifest.json` and then pass that same path to the audit command. Do not capture over the committed manifest. The first exploratory audit against Windows checkout bytes is preserved as `evidence/audit_result.json` and `evidence/predecessor_artifact_manifest.json`; it returned HOLD because checkout line-ending conversion changed hashes. The corrected audit reads predecessor evidence from Git blobs, not the Windows checkout. The contact sheet is a human-readable rendering of those hash-verified raw pixels; it is not a new GUI observation.
