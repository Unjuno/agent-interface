# Versioned A02 raw audit repair V3

Audit V1's source/input hash-map assumption and audit V2's receipt-field
assumption are both preserved with their raw reports. Audit V3 changes only
the closure check to read child return code and pipe counts from
`RUN_RECEIPT.json`, and reader errors/join status from `RESULT.json`, matching
the candidate's frozen record layout. It rechecks the exact same A02 bytes and
does not rerun the child.
