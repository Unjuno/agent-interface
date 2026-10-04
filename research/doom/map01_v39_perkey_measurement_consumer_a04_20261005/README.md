# V39 per-key measurement consumer A04

A04 is a narrow, offline exact-type regression for the owner-bracket interval
join in A03. A03 remains byte-for-byte unchanged. Its candidate and independent
auditor accepted a bracket endpoint changed in memory from an integer to an
equal float for both physical down and physical up; Python's equality treats
`1.0 == 1` as true. A04 requires each edge and owner interval to be exactly two
ordered nonnegative integers before equality can join them.

The retained A03 input pair is the sole test input. A04 baseline reconstruction
agrees across separate candidate and auditor implementations. Float aliases on
both edges, boolean aliases on both edges, a mismatching integer interval, and
a malformed interval are rejected. Normal and optimized Python each pass all
four regression methods. The independent audit verifies the A03 frozen source
and input hashes remain unchanged and reconstructs the exact baseline pair.
Commands, test transcripts, and audit output are in `results/a04/`.

This is only a consumer-boundary source-contract result. The pair comes from a
fake-display harness; no live GUI, game, model, useful feedback, threat
response, recovery, or MAP01 outcome is observed. No physical occupancy or
application effect is claimed. See `PLAN.md` for H/T/D/C/U and run boundaries.
