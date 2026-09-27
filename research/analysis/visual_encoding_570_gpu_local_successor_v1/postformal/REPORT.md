# Post-formal publication and auditor corrections

This append-only supplement addresses two review findings on PR #4737. It does not edit the frozen v1 sources, original `AUDIT.json`, formal request/response records, or inference result. No model or network request was made for this supplement.

## Frozen payload publication

The GitHub Contents publication path added one terminal CRLF to non-empty text payloads. Direct raw-byte comparison therefore failed for `FREEZE.json` and other payloads, even though removing exactly one terminal CRLF restored the preregistered bytes. GitHub MCP base64 readback independently checked all seven frozen source files and all 34 entries in `EVIDENCE_MANIFEST.json`: all 41/41 match their original SHA-256 and, where recorded, byte size after removing that one terminal CRLF; no payload had any other mismatch. The two empty log files remain byte-identical. `FREEZE.json` itself becomes the preregistered 2,605 bytes / SHA-256 `8d8c337e...`; `EVIDENCE_MANIFEST.json` becomes 6,482 bytes / SHA-256 `c0f6c8a2...`.

`verify_transport.py` verifies the original freeze/manifest/source/evidence hashes without modifying a checkout. Its optional `--materialize <new-path>` first verifies everything, then creates a separate copy with only the verified publication suffix removed from managed files. It refuses an existing destination and destinations inside the source tree. The original checkout and published evidence remain unchanged. A pinned local helper Docker test simulated the GitHub byte representation, verified all 41 content payloads, materialized a separate copy (42 CRLF suffixes including freeze/manifest/sidecar), and re-verified the copy.

## Corrected score semantics

The original v1 auditor labels any positive prediction below IoU 0.5 `positive_box_invalid` and turns it into HOLD, which incorrectly mixes an ordinary localization miss with integrity/GPU failures. `audit_v2.py` is a separate post-formal scorer: a well-formed positive box below threshold counts as a miss; malformed boxes and every other integrity/GPU error remain HOLD. Regression tests prove one miss plus five hits passes the declared >=5/6 gate, two misses fail the capability gate, and a malformed box remains HOLD.

Applied to the unchanged eight formal records, v2 returns `PASS_DIAGNOSTIC_SCOPED`, 6/6 positive hits, 2/2 absent abstentions, no errors. This agrees with the observed result; it does not increase the claim or change any inference data. The originally published v1 audit remains preserved as historical output.

## Verification

- Pinned helper image: `sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261`, `linux/amd64`, `--network none`, read-only root/source mounts, no GPU device request.
- 10/10 unit tests pass (four original v1 tests, three v2 scoring tests, and three transport tests).
- Original formal raw-data re-audit completed in this same helper image; no requests were issued.
- Source hashes for this supplement are recorded in `POSTFORMAL_RESULTS.json`.

## Scope

This repairs publication byte verification and scoring semantics only. It does not repair the original launcher’s post-run Windows log-decoding failure, validate model training, test a real application, establish CPU-vs-GPU latency causality, or justify product/safety/action-authority claims. The PR must remain unmerged until the normal required PR checks are green and the head branch/commit is revalidated.

