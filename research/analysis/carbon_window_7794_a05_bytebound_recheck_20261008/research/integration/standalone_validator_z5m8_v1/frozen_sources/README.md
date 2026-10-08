# Original validator source snapshot

The five packaged source files were restored from the Git blob IDs already
recorded in `../BASELINE.json`. The remaining original engineering inputs were
restored from Git and checked against `../FREEZE.json`. All 15 frozen inputs,
including builder and audit code, match the existing SHA256 values. No baseline
hash, original artifact, raw observation or audit result was changed.

`../verify_retained.py` reads this snapshot to reconstruct the historical
artifact. It still checks the existing hashes and compares the reconstructed
manifest and all 500 audit checks with the original records. The audit runs in a
temporary reconstruction of its original source tree. This snapshot is archival input,
not the source shipped by the current runtime builder. The standalone-validator
workflow also runs the current `test_validator_zipapp` suite before reconstruction.

Using the current working tree for both tasks prevented contract evolution:
adding optional window activation changed contract.py and made the historical
source identity check fail even though its original observations were unchanged.
