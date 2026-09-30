# Public guarded observation references: construction/replay checkpoint

Existing native receipt references inspired a bounded public-response variant.
The optional observation_refs flag is now wired to guarded observe, guarded input
and retained results. It defaults false. This checkpoint has no new live GUI use;
it is not approved evidence for model utility, tokens, speed or human tempo.

The projection replaces only observation_report.observation with a listed local
reference to source.native, when exact canonical JSON and observation IDs match
and the result is smaller under the public text serializer. The canonical object,
image, other fields and raw report remain unchanged. Reserved caller metadata,
near duplicates, refused/persistence-failed reports, and unsupported brief results
stay literal. The decoder accepts only the fixed local mapping, not arbitrary
pointers. It restores the presentation view exactly; if detail=brief was also used,
that view still contains lossy guard summaries and is not the full raw report.

Offline replay of all 30 replies in guarded-mint-many-primary-02 reduced returned
text from 114,160 to 103,143 UTF-8 bytes (23 referenced replies; 9.6505%). Every
expanded JSON matched the original, and original serialization was reproduced.
No image payload was altered. These are same-record bytes, not actual model tokens.
The prior live run did not see this representation and must not be relabeled.

255 protocol and 106 harness tests passed, including full/brief round trips,
near-duplicate type distinctions, reserved names, invalid reference decoding,
image parity, read-after-close, and no recapture/input on retained lookup.
The archive binds the exact construction sources and full check logs. Two
accidentally broad docstring replacements and CRLF diff warnings were corrected
after checks; these corrections change documentation/line endings only.

Next gate: primary-model use of the portable artifact, including perception of
local references, text review before Save, independent scoring, refusal detail,
retained full retrieval and release. Keep this branch unmerged until that gate.
