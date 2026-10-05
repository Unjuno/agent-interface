# Historical parent and candidate source

These two snapshots are separate versions and must not be conflated:

- `parent/input_owner_v12.py` is byte-identical to parent commit `0f50064a7ea7a69c51cb6751ac313b0c8b5ec9e2` (Git blob `83f21cec065340d6fd5ad006979bfba0f13d62bc`, 16,387 bytes; SHA-256 `09cc23e67e6a3de1b0029fbb0184cdf54d3d8e29561281870d2b0b76027511d8`).
- `candidate/input_owner_v12.py` is byte-identical to the one-shot candidate commit `f5847058846755c5622631758edc7cdfd9bc2b77` (Git blob `64eb6ee206312c0b6c281b9565c0367631d28444`, 16,742 bytes; SHA-256 `f46dd62edd085afe29fe031f74a31397bb568f583affde0a26ac79686625d433`).

Both originals referred to `research/live_control/input_owner_v12.py` in separate historical trees. The A01/A02 `SHA256SUMS.txt` source-path entry names the candidate bytes, not the parent bytes; the unchanged manifest is checked against `candidate/input_owner_v12.py`. The parent copy separately preserves the hash cited by the H/T/D/C/U records. Both copies are data snapshots under the retained result directory, not active runtime modules, and neither was executed during rescue.
