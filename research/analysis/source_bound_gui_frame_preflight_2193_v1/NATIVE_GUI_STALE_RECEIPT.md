# Native GUI stale-receipt gate

On the 120-frame native clutter dataset, step order and receipt labels were checked.

- normal sequence: `(True, pass)`
- one frame given the prior step's receipt: `(False, stale_or_reordered_receipt)`
- two adjacent receipts reordered: `(False, stale_or_reordered_receipt)`

The canonical dataset was not modified. This gate rejects stale or reordered provenance before model evaluation and is separate from pixel-hash integrity.
