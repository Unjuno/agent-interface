# Additive lifecycle dependency-byte reconstruction on Linux

Disposition: **PASS_EXACT_REFERENCE_RECONSTRUCTION_SCOPED**.
This follow-up resolves the dependency representation question raised by
[the retained Linux intake HOLD](../lifecycle-intake-01/README.md). It does not
erase that failed native Git-byte check or make an unmodified Linux checkout pass.

## Preparation and unchanged inputs

The integration owner copied the exact source snapshot retained from main
`0c1e87b454fb70bcc7b11dbb8b6a719512d0425b` to a fresh dedicated directory.
Only the two declared reference files were converted from LF to CRLF, and each
output was required to match its already-frozen SHA-256 before anything ran.
The candidate code, original FREEZE, skill/expected inputs, formal raw,
historical audit and prior corrected audit were copied byte-for-byte.
No original snapshot, frozen record, shared dependency or .gitattributes changed.

The mapping is explicit in reconstruction.json. It is a derived reconstruction
of measured byte identities, not evidence that the original Linux checkout had
those bytes. The predecessor's checks and STOP remain intact.

## Results

1. Ten existing construction/correction tests passed, including frozen source
   and reference identity plus both 12,288-prediction checks.
2. A separate invocation of the existing corrected raw auditor passed:
   `PASS_CORRECTED_RAW_REAUDIT_SCOPED`, 30,000 reconciled predictions, zero errors,
   15/15 paired wins, seven mutation controls rejected, median break-even 1.
3. Every field of the generated corrected audit equals the previously retained
   corrected audit except auditor_python, which correctly records this Linux
   interpreter instead of the earlier Windows interpreter. This includes source,
   input and raw hashes, all block ratios, all break-even values and dispositions.

These are read-only checks of the consumed formal raw. No new performance trial,
Docker, GPU, model, GUI, X11 or input allocation was run. The original formal
timings remain the source of the ratios; Linux test elapsed times are not a
new performance comparison.

## Integration decision

The specific reference-byte mismatch is now explained and reproducibly bridged
by exact-byte reconstruction. The corrected synthetic lifecycle result can be
read with that mapping and its stated scope. A plain LF checkout still fails
the original byte gate; do not silently relax it or overwrite its expectations.

This result supports only the retained synthetic scorer lifecycle hypothesis.
It is not a measured improvement to MCP, capture, input, semantic feedback or
model token cost. No runtime behavior is changed. The existing persistent-X11
route already reuses its owned connection; a new reuse proposal must identify
remaining per-request work and measure it at the actual primary interface boundary.

The archive contains the complete derived source/data snapshot, test/audit logs,
commands, reconstruction mapping, corrected audit and field comparison. The
verifier compares it against the predecessor archive and checks that only the two
declared line-ending changes occurred. It does not execute retained source.
Run `python3 -O runtime/results/lifecycle-reference-reconstruction-01/verify.py`.
