# A01 retained STOP

The sole frozen A01 candidate invocation exited 1 before producing a candidate
result. The candidate's frozen SHA-256 literal has a transposition at hex
positions 15–16; the exact input file is consistent with the source Git blob
and its independently computed SHA-256. The one-shot `results/a01/` directory
was created before input validation and is retained with STOP evidence.

No A01 retry was performed. Any corrected execution requires a separately
versioned successor freeze and output path. This is a source-pin/setup failure,
not a negative result about whether the V12 measurement schema can be consumed.
