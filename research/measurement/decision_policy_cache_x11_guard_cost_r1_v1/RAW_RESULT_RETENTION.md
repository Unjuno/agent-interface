# Raw-result retention boundary

The formal first-outcome `RESULT.json` was produced exactly once in the disposable container.

- bytes: 635906
- SHA-256: `9b2f0900326684a9203306648bb672c80626a89251945ecb9da3f3ea09e2198b`
- deterministic gzip bytes: 44277
- gzip SHA-256: `eafe6d8b76b1dd056c5d361e50bcfae9a230028bd906e9a5105d959b80568f9f`
- base64(gzip) bytes: 59037
- formal invocation: 1
- reruns: 0

The GitHub connector accepted the compact source/audit/summary records but byte-for-byte verification failed when the large raw archive was manually relayed through chunked connector arguments. Those mismatched blobs were not added to the retained tree. The repository therefore retains the exact raw-result digest/size plus the independently recomputed summary and audit, but not the 635,906 raw JSON bytes themselves.

This is a retention/transport limitation, not a scientific rerun or substitution. No metric, threshold, source, seed or decision was changed after the formal run. A later archive transfer may attach the raw bytes only if it reproduces the SHA-256 above exactly; it must not regenerate the experiment.
