# Additive deterministic audit correction

The Issue2789 / PR5639 read-only audit reported that the historical
post-release-spine-02 verifier depends on directory enumeration order. That
report is reproducible: forcing ascending `Path.glob` order makes the original
verifier fail `analysis mismatch`; natural enumeration on this WSL checkout
happens to pass. The original analyzer appends refusals in reply-file order,
while retained analyses list attempts `[16,14,17]`.

`verify_v2.py` preserves every original hash, effect, release, review, source and
usage check. It compares deep copies with only each route's refusal list sorted
by its unique integer attempt. It drops no fields or rows. The canonical list is
`[14,16,17]`; every other value must still match both archived and published
analyses exactly. The old verifier/analyzer, archive, manifest and frozen
analyses remain unchanged. This correction does not certify new live outcomes.

The new regression verifies the actual 617-member archive under both forward
and reversed enumeration, comparing identical corrected results. Normal and
`-O` corrected verification pass. The original five controls still reject
archive corruption, missing member, wrong independent score, wrong review
image and refusal claiming input. The regression first failed because this
additive auditor did not exist.

The historical manual 6/6 pair and **HOLD_INTEGRATION_INCOMPLETE** gate are
unchanged. Automatic/current-source recovery, matched economics, broader
domains and human-comparable tempo remain unproved.

```sh
python3 runtime/results/post-release-spine-02-audit-v2/test_order.py
python3 runtime/results/post-release-spine-02-audit-v2/verify_v2.py
python3 -O runtime/results/post-release-spine-02-audit-v2/verify_v2.py
python3 runtime/results/post-release-spine-02-audit-v2/controls_v2.py
```
