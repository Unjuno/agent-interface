# A03 supplemental audit result

Disposition: **PASS_AUDIT_CONTROLS_RECONCILED**. Auditor invoked once, exit 0; candidate invoked 0 times; retries 0. This supplemental result does not erase A01's or A02's terminal execution records.

Exact command:

```text
python3 audit_controls.py --input ../conditional_parallax_6079_layer_identity_a01_20261003/fixture/public.json --truth ../conditional_parallax_6079_layer_identity_a01_20261003/fixture/auditor_truth.json --raw ../conditional_parallax_6079_layer_identity_a01_20261003/results/formal_01/candidate.raw.jsonl --expected-public-sha256 8614e740c5651471c957ece8df6728f10996e4e24ded12ef2eed21fcf90a45b3 --out results/audit_controls_01/audit.json
```

Stdout: `status=PASS_AUDIT_CONTROLS_RECONCILED rows=8 corruptions=5`.

The independent auditor reconstructed all eight raw rows and reconciled the auditor-only truth: two DISTINGUISHED cases and six UNKNOWN controls. The foreground-dominance sham retained all-feature squared gap 784 and layer-relative squared gap 0. All five corruption controls returned true for their exact preregistered rejection reasons, including an actual foreground relabel (the A02 no-op was corrected).

SHA-256:

- A03 audit output: `4badab8770af7a9826616886bba8ce12c7aab8693d46a0d3cb73fa9c1a1d900e`
- A03 auditor source: `fb5aeff698f2cf6c5251084f18ad73247cb530c6dc757dd9ef01bbd22234d07c`
- A01 candidate raw (unchanged): `4e4f95a92add0cc8f19ae7f10725e21905ab81116f7db17847e0abd26fc277d0`
- Public fixture: `8614e740c5651471c957ece8df6728f10996e4e24ded12ef2eed21fcf90a45b3`
- Auditor-only truth: `9f41feb02e9871415bb9492a88f5ed0a3676e7c7bff79b44d52358fd8808fc6d`

Scope remains the authored finite 2-D fixture with stipulated identity labels. No real-scene identity provenance, contact, GUI/game, safety, task benefit, or generalization claim follows.
