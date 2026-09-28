# Source-byte publication repair — append-only

The original Windows/Docker formal used the exact mixed-line-ending source
bytes whose SHA-256 values are in `FREEZE.json` and `formal-04/raw.json`. The
initial PR commit normalized five Python files to LF in Git. The source text
was unchanged, but fresh Linux checkouts therefore failed the frozen byte-hash
preflight. `git ls-files --eol` on the original publication showed `i/lf
w/mixed` for those five files; direct GitHub raw readback was LF-only. Removing
only CRLF carriage returns made the five source files byte-identical (5/5),
confirming a line-ending-only publication defect.

This repair preserves the exact measured bytes with the path-specific
`.gitattributes` `-text` rule. It does not change the historical freeze, raw
formal result, or original audit. The `source_git_blobs` in the original freeze
are retained as the normalized blobs present at first publication; the table
below maps them to the new exact-byte blobs. SHA-256 values remain the frozen
values and are checked by the existing test suite and corrected raw audit.

| Source | Original normalized Git blob | Exact-byte Git blob | Frozen SHA-256 |
|---|---|---|---|
| `README.md` | `996aeae48e63cdb2f55f3def8c13612ac78fc3b8` | `996aeae48e63cdb2f55f3def8c13612ac78fc3b8` | `8f043e3a57de18639a4a78248301ca2511d5fd5068c5cae4f229efa9e15405ec` |
| `lifecycle_corrected.py` | `879accfdaa77e9d2f4c82c5bfa30ba7743fe3a3c` | `898e65d4503b95ebdbd02e00bceaf8c37ef5b754` | `f2b0c70547603ac665c8053b1e5b9181dce49df6a92837922adb450cf1adabe4` |
| `test_lifecycle.py` | `b5d8dc5bb292f0e22bfebfebd3d30aaae888a3f2` | `e6380410c1cfc460bfefa14491438b211e06a5ab` | `0ecc51b7515d7332889e8b84736896df20faf67a5420b83b10ee18b5e517c767` |
| `construction_runner.py` | `c897a7d38c46862e40a8326f26cecdbcc8cdb468` | `650e0db2f9618712b1827580664ed7a10037b3d0` | `738dfe28d4a527a4db6915555d972b6a053ad851534cf3c56135a1473dd61745` |
| `formal_runner.py` | `b3da61e5566beca47509df697c0944d5b7b2b71c` | `e1682c123a6bba55d3a55b2d857dee5cf6858363` | `2f7d0149e85b8f1a7770536c96659fc7476fdd75af21a04728ece5f9b7be25cd` |
| `audit_raw.py` | `bb815e4df3ddf43e16bb28ae7aaecd8a7fe557fb` | `f30c7d46561c812280d2fc8ea8c34a18d4236c91` | `b149d0e803b1421a1e221ee021786f75d0a4c942cd4ba355d79f668bd26b0f87` |

`audit_correction.py` records the exact-byte blob IDs in its supplemental
report and independently reconstructs the immutable formal raw. No formal
runner or Docker container was relaunched for this publication repair.
