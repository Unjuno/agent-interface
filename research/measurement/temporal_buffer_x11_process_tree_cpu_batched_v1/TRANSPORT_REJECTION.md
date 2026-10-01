# Transport rejection

The original single-file `source_bundle.tar.gz.b64` transport is **noncanonical**.
It was rejected before any formal pair because its remote Git object did not match the tested local source text.

Canonical source transport for #1262 is:
- source.part00.b64 `c39a6bcf26a62f7bbf8f07437d9d2af6164baf3c`
- source.part01.b64 `4bb500fa59f0fa62ac40a4bb6b8131ee2b21a3ae`
- source.part02.b64 `0fc5ee3cba2975b734b5075bb6257708404fbfb3`

Concatenate these parts and use `reconstruct_source_parts.py`.
The decoded gzip identity remains SHA-256 `e160e21f5c0ec3981c8c3d9b58b65bfdcf700973f2a8493bba4b30a95c03fd87`.

No scientific source, threshold, schedule or formal row changed. Formal pairs at rejection/fix: 0/8.
