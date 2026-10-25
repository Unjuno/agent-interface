# Shared immutable S29 input manifests

This directory holds one canonical copy of the five content manifests and input summary reused by S30-S35. Each attempt's source freeze records the same manifest digests. The actual large asset trees remain at the preregistered local asset paths; this packet preserves their file inventory and hashes without copying the 479 MB repository/dependency/stage trees into Git.

| Manifest | SHA-256 |
|---|---|
| `INPUTS-SUMMARY.json` | `fcb0ee88e1136e3496511dd6a1e1b01148a8688f359c73c1d5b3a14afbb5d5d5` |
| `REPO-MANIFEST.json` | `d7526199a2ba46a991e5d677ccc7b829814a7cb71c74ab825ef5d334c6eb4741` |
| `DEPS-MANIFEST.json` | `94e1ae5ec5138be6af4c5cf8d9f0a4162be252faa719159ef27c43cd95041e53` |
| `STAGE-MANIFEST.json` | `d6f58b39e5753aa845049d540a515d8f29b07b3f7a18979439dfb3624facab20` |
| `XKB-MANIFEST.json` | `dd7411e7ca7a17a3aa1706f79f015f5ac33e9400da4f04e7d895803e496193d3` |
| `RUNNER-MANIFEST.json` | `376f69d98a391e66916ca6d68570b2e6c1f40e62951333bf1347706b1f7f90d5` |
