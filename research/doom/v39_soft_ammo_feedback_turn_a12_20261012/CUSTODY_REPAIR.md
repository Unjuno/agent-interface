# A12 package checksum repair

The original 19-entry `SHA256SUMS` was checked against the exact Git blobs in
the retained PR head. Twelve entries matched. Seven entries matched only after
converting the Git LF blob bytes to CRLF, showing that those digests described
newline-translated working-tree bytes rather than the committed package bytes.
The current-main successor changes only these seven manifest values to the
SHA-256 of each exact retained Git blob:

| File | Original listed digest | Exact Git-blob digest |
|---|---|---|
| `results/audit.json` | `92539a632323a70dd2d8d75e6300c54ae3fc369e77d16f920782c9056263bd03` | `bedacd6b9aca1c6ab40a1e31d3de1d6b99bdddc6c0b31321b48ff4540b28113a` |
| `results/environment-probe.txt` | `540f172ece6adf292f67ba60948a51c05d37080d981c1e6fb9782dc8af2096fd` | `ea0c92e1298136d26ab220f03f00eb92d3bfc041e1b9fcf18ae68e8b1c3e0c68` |
| `results/environment.txt` | `e5fa8f4b8319555e69cb2a92119be99b66c644468879b9aed879b6d975d60e00` | `d11f21b27d8cbc8d6eee7f1cb20a4249305cf5cecad974c7ee6b4fbbe985fe4d` |
| `results/exit.txt` | `13bf7b3039c63bf5a50491fa3cfd8eb4e699d1ba1436315aef9cbe5711530354` | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| `results/feedback_receipt.json` | `a59808dacaa0b16b74816c7eaf7b838053e8a6ca681f6b131ab2c2894f57206b` | `8ee89769aa36fab1a8267c75fb3106dbce2a1cd3eab7faf4f35550670cdd0583` |
| `results/wslc.stdout.txt` | `039dc266464ead4133cf5e3dd6251827e5134db8f907da08b389a44b2b1a7165` | `ce1998457f27ac6dfaf31a9b824dbf26910b2dbc68e2246027d76ba3b05e27f7` |
| `source_hashes.json` | `98dca9b0c2b9fa697e3e747b5e2852dc5426312a1765b862d7284cafd8a46794` | `564a65941f86997d8e51c62f1a98f1c9ec8f6a082458ca10009838002c9c4657` |

The other twelve original members matched their Git-blob digests. The repair
does not rewrite any raw transcript, receipt, environment record, frozen source,
test, or saved audit, and it does not rerun the test or consumed WSLc allocation.
The saved `PASS_SCOPED` audit remains the result of record; its limits are in
the packet README.
