# Remote source freeze receipt

Task: `SEMANTIC-PINCH-CROSS-BACKEND-20260917-001`
Issue: #681
Publication BASE: `387bf48955773f51c509d0a4b9eb3e39b593511c`
Formal browser cases executed before this freeze: **0**.

Deterministic source archive: `source-freeze.tar.gz`
- bytes: 6,087
- SHA-256: `8053114c17a666043f9698e36e2e69676955a1987043b8037a7511c19e5273ba`
- local Git hash-object: `ea741875b9cd1d64c40d526b02255e2435aeebb0`

Canonical GitHub transport is ten Base64 text chunks. A prior monolithic binary-blob upload and a prior 3-part transfer did not match the local Git object identities and are unreferenced non-evidence.

Verified chunk Git blobs, in order:
1. `ad951c031dce745eb652c7a5e5cd2c9c4b1ff236`
2. `d8e7a59164c7aebe6ff9ee048f054785f6ad3918`
3. `4479384241c3269ad0f68641f08ae0b16faf1c43`
4. `40c44a41d8f6578c083ce7d030cf77bdeff87cf4`
5. `328acb3c764d6acbe2d447e8165d7f1a92c6795d`
6. `397f15711bf51e2ad544b47be970eb66ea8a8cc4`
7. `08d7fdfeb40969c54fe3de53202fdbb876b3be28`
8. `c88b13f0fe4853045aaf0b510ba65c484c44bf20`
9. `e3405ffcc6d69c496804405c0b75178358333c96`
10. `307d93656073489bb8a6b230b644ba89c7fcc173`

`reconstruct_source.py` concatenates those chunks, Base64-decodes the archive and refuses output unless the exact SHA-256 above matches. The archive contains the ten preregistered source/plan/hash files listed by `source_sha256.txt`. Formal may begin only after branch readback confirms this canonical transport.
