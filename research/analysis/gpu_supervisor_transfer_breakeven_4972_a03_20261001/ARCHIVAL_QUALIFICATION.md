# Archival qualification — allocation 03

Preserve this consumed allocation as an integrity HOLD. The candidate ran once;
the independent auditor ran once and rejected integrity because the frozen
`unsafe_admission` corruption control changed 1 to 1 and therefore tested no
corruption. Do not rerun either process or alter this allocation's source,
outputs, audit, or verdict. Any follow-up requires a new allocation and freeze.

The candidate bytes are retained as eight base64 shards with the exact byte
length and SHA-256 in `raw_evidence.manifest.json`. `candidate_result.json` is a
pointer, not the reconstructed result. This archive is not an accepted
CPU/CUDA crossover result; timing medians are descriptive only. It makes no
production or broader performance claim.
