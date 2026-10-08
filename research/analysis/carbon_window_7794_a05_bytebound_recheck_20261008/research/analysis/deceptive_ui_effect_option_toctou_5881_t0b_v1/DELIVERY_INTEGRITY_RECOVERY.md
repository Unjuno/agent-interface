# Exact-byte delivery recovery

This additive note records a transport repair for the evidence in this directory; it is not a new experiment and does not change the scoped result.

The original PR head was `5ccfcd0477aaae5900f8827c04d86a2908b6ddeb`. On its committed Git blobs, `results/audit.json`, `results/decisions.jsonl`, and `results/effect_events.jsonl` were LF-normalized and did not match their frozen SHA-256 values in `SHA256SUMS.txt`. Converting each committed file's line endings from LF to CRLF reproduced its recorded SHA-256 exactly. The remaining tracked, non-bytecode entries in that manifest matched directly.

This recovery preserves those three exact CRLF byte streams and adds a targeted `-text` rule in the repository `.gitattributes`, consistent with the repository's exact-byte policy. No candidate or effect simulator was rerun; the retained inputs, row content, audit disposition, and residual post-admission race are unchanged. Note that `audit.py` rewrites `results/audit.json`; an audit rerun should use a disposable copy or restore and reverify the frozen artifact afterward.

The original manifest also lists four `__pycache__/*.pyc` files that are not tracked in the original PR and are absent from a clean checkout. They are not reconstructed or treated as research evidence. To verify every tracked manifest entry, check the manifest while excluding only `__pycache__/` entries.
