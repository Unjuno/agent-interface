# Cover-policy contract repair v2

The first frozen corrected-threat exposure was retained without rerun. Its first
Astra call completed and its primary forward program completed. Astra authored
`coast pulse` for the next inference interval. Controller v20 expanded that into
twenty 500 ms coast steps, so the shared executor rejected `cover-1` at its
1–16-step admission gate. No rejected-cover input ran and no post-control score
was available.

V21 clamps coast chunk size so all four legacy coast extents fit ten seconds in
at most 16 steps. A two-decision live smoke completed with no rejection. That
run happened to author `coast short`; `coast pulse` is covered by the exhaustive
compiler check rather than a selected successful model sample.

An attempted schema v2 used `oneOf` to make coast-only and active cover mutually
exclusive. The actual response endpoint rejected `oneOf` before a model message
or primary input. Schema v3 removes that compatibility hazard and simplifies the
representation: an empty `next_cover` means coast, while array items permit only
backward, strafe, fire and retreat-fire. Mixed coast/action policies are therefore
structurally impossible without conditional schema features.

Controller v23 maps the empty array to two five-second coast steps. The schema-v3
endpoint probe completed two Astra decisions, both returning empty cover, with
two accepted ten-second cover programs and zero rejection. An exhaustive property
test passes every one of the 168,421 policies permitted by schema v3: total
duration exactly 10,000 ms, at most 16 steps and a final coast.

The earlier eight-decision corrected pilot is retained as an unexposed result:
it reached the opening door but saw no threat, so every policy was coast. It did
exercise two local no-effect contingencies at 128.303 ms and 110.676 ms. The
second branch skipped one remaining primary command. Neither this result nor the
contract probes establish threat-policy gameplay benefit.

The next bounded threat exposure must use schema v3/controller v23 under a new
allocation ID. The frozen v20 allocation remains failed and is never rerun.

Run the audit and exhaustive test with:

```sh
python research/doom/audit_map01_cover_contract_v2.py
PYTHONPATH=research/doom python research/doom/test_map01_cover_compiler_v2.py
```
