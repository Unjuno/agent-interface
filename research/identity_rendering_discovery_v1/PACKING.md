# Complete retained evidence

The four numbered files are consecutive BINARY chunks of one XZ-compressed TAR, not base64 text. Concatenate in numeric order, verify the full digest, then extract into a fresh directory. The archive contains all 42 retained files, including executable bench.py, exact a1/a2 sources and setup failures, imported production-research source snapshots, 120-pair raw JSONL, all screenshots and integer timing endpoints, manifests and independent audit. No font files are included.

```bash
cd research/identity_rendering_discovery_v1
cat evidence.tar.xz.parts/000 evidence.tar.xz.parts/001 \
    evidence.tar.xz.parts/002 evidence.tar.xz.parts/003 > evidence.tar.xz
printf '%s  %s\n' \
  4c19667b989b61d446e53c3494eeb6e95bce930171757fb9e1d5726d7b96e4bb \
  evidence.tar.xz | sha256sum -c -
tar -xf evidence.tar.xz
python identity_discovery/audit.py identity_discovery/third_run
```

Do not run Python with -O: audit assertions must remain enabled. Offline audit needs Pillow and NumPy (measured versions: 12.3.0 and 2.3.5). A new live experiment needs a new allocation/source freeze and a fresh output directory; do not reuse consumed a1/a2/a3 IDs.

Whole archive: 35,312 bytes, SHA-256 `4c19667b989b61d446e53c3494eeb6e95bce930171757fb9e1d5726d7b96e4bb`.

| Part | Bytes | SHA-256 | Git blob |
|---|---:|---|---|
| 000 | 9000 | 3411bfedbab49fccdefb190630d2aea816d3d50b3fa00f19d86c433b1fab11c0 | e2fe81748cdc7ee256898395c0badc394c17db3d |
| 001 | 9000 | 6cc4614dfd69cd4a99f7eb90c29cf3b6994a2b910d31c074e097b88abf82da9e | 5606683f743263b7605d52a471603cdf73eeca20 |
| 002 | 9000 | 14c7c3c33cf42281299eb38f0ff10b46375bd5ff381f9e4b350c61d27dc958b0 | e17a131f8c62b02930f1c3316bea6aa90823cd41 |
| 003 | 8312 | b5266fa50363bbf46a2dcd1dad09006c989e2393705f84bd537b43ee1ec91929 | 1eab6b672b0525b4845134f2657f2897bd84e5be |

Each uploaded Git blob hash matched its locally calculated identity. Recombination was locally verified against the archive; all 42 archived files matched their retained local bytes. REPORT.md and audit.py are also readable directly in this repository directory.
