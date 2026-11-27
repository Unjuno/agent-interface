# Additive custody correction — 2026-11-21

This correction preserves, and does not edit, the original 2026-11-04 result or its manifest.

The PR #10218 head `b1e24401ca0817ed4504b62f9c7190a0c900735a` stored `commands.txt` as 738 bytes with SHA-256 `409af0a0e70852c2b2125c9e3f9b050980b870e2902738dc7406a1a4a809da55`, while its retained manifest expected 739 bytes and SHA-256 `275ed1967585d05064c1cd7d6dc0c80706b518987d1a0b65155584105ad15750`.

A deterministic one-byte recovery enumerated every possible insertion position for a single CR in the stored file. Exactly one position (offset 737, immediately before the final LF) reproduced the manifest's expected size and full SHA-256. This yields a CRLF final line ending. The candidate copy now contains those recovered bytes; the old PR head remains unchanged. This is checksum-guided byte recovery, not an inference about the command's execution result.

After restoration, both transferred evidence manifests were rechecked against current bytes. The correction itself is additive and is intentionally not listed inside the historical manifest it corrects.
