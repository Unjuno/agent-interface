# GitHub source identities — construction probe

Read-back GitHub blob IDs from the successor branch:

- `source/runner.py`: `4d485ec748299cc26c9c9ec321a6c5ab3ce41b4c` (local SHA-256 `A2064F69E802D8A3ACE6CEDAD4368EA59CF7AD9926432023298466BB0FDC415D`)
- `source/audit.py`: `f064f28e73104ed9e071e3f193ea3d17903342c5` (local SHA-256 `A1843E24B8D538BFA45B78C0C0E62FE8EFA756FCC0B35CC97089F4F2104C85DE`)

Git blob IDs identify the bytes stored by GitHub, including the content API's terminal newline. Local SHA-256 values identify the corresponding source before that transport normalization. The raw artifact is stored as 28 ordered base64 text parts of a gzip stream; `assemble_raw.py` reconstructs it and checks the exact uncompressed byte length and SHA-256 before audit.

