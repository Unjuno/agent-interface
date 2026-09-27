# Pre-emission audit allocation #3015

Fresh Docker allocation:
- image `agent-interface-2994:20260920`
- digest `sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c`
- `--network none`
- useful control and distinct-XID replacement/source-mismatch rows

Verifier result:
- useful control: XTEST ledger 35, release verified
- target replacement: XTEST ledger 0, backend emissions 0, release verified, raw runtime preserved as execution_failed/unknown
- source mismatch: STALE_BINDING, zero backend execution
- narrow audit decision: `PRE_EMISSION_FAIL_CLOSED`

This is a research-only audit classification. It does not rewrite the promoted runtime result, and it does not claim broad desktop acceptance.

Hashes:
- audit summary `a269447faf2d56cf0c82def14e91208e7b21c17376006ea9415ab8575d863919`
- useful ledger `a766dc9868a0b6fddd9065884225b496b6f3f8e17ed8e12a77529004047c4ee2`
- verifier `89739b6d7b69c0f146b5a3297fe32485adc1fd8f040bb36c47342715ef54ef0d`
