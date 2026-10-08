# Evidence transport note

Canonical evidence archive SHA-256: `352f79424bb241e67dd921a0049ece008268c59e87a469c3eec8b8dc7331c57e`.

GitHub publication uses three Base64 text parts plus `reconstruct_evidence.py`. `evidence.part01.b64` and `evidence.part03.b64` match their local Git object identities exactly. The Contents-API publication of `evidence.part02.b64` omitted only the final newline: remote size is 6000 bytes / Git blob `28c7c76029ee3fcdacb42ce55d7e92579f21ffc6`, which is exactly the local 6001-byte part with its final `\n` removed. No Base64 character differs.

The retained reconstructor deliberately applies `.strip()` to every text part before concatenation, so the newline-normalized remote parts reconstruct the exact archive bytes and verify the archive SHA above. Do not describe part02 itself as byte-identical to the newline-terminated local transport file; the evidence archive identity is the canonical boundary.
