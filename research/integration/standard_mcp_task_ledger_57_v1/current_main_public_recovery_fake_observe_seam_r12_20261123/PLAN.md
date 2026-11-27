# R12 corrected supervised Fake observation seam check

R11 reached the patched fake exactly once and its raw observation receipt carried the unique marker and `input_dispatched=false`, but the test failed because it also treated an outer receipt-view envelope field as the raw observation's dispatch state. This was an invalid assertion; preserve R11 and do not retry it.

R12 checks the frozen requirement against the raw observation report only: callback count 1, unique ID, `side_effect_authority=false`, and `input_dispatched=false`. Run one normal and one `-O`, fresh process each; no retry.
