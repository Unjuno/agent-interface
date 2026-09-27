# Source publication incident — pre-primary, no science rows

Initial `SOURCE_FREEZE.tar.gz` upload through a manually relayed single base64 payload did not reproduce the local Git blob on remote readback. Local blob was `74d9d085659bfc56a79cfcc0db5433e6e7c6a154`; remote blob was `7b7fc6fad962e8174099c732df873d293ab8a657`.

`FREEZE.json` itself read back byte-exact (`e5de6f822b2b191f201e9d757bb35e48c2defedc`). No primary row or invocation existed. The mismatched binary was deleted from the branch. Scientific source, schedule, seed and decision gates remain unchanged.

Setup-only repair: publish the exact same local source archive as ordered UTF-8 base64 chunks, read back every chunk by Git blob, reconstruct locally from the remote-text identity, and only then authorize primary.
