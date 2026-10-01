# Recovery status for #4064 first-rung delivery

The five original delivery metadata files are preserved unchanged. The
`PATCH_MANIFEST.json` names 17 `full_patch/part-*.patchpart` files, but none is
present in the old branch or current main. Running the supplied
`reconstruct_patch.py` fails on missing `full_patch/part-00.patchpart`; the
claimed 814,758-byte patch and 66-file evidence namespace therefore cannot be
reconstructed from this branch.

`RETAINED_RESULT.json`, `README.md`, and `PUBLICATION_NOTE.md` report a scoped
24-case PASS and state that the original bundle was audited with 10/10
corruption controls. Those are preserved as historical reported claims only;
the underlying patch/raw bundle was not available for independent audit here.
The separate later 36-case dependency-budget result remains a distinct
publication HOLD and is not replaced or upgraded by this record.

Disposition: `HOLD_DELIVERY_PARTS_MISSING`; no scientific rerun or evidence
reconstruction was made.
