# Amendments before repeat

2026-10-03: Original image digest transcription was invalid (63 hex chars) and candidate launch was rejected before creating a container. Valid pulled image inspected in the isolated WSLc session: python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016; image ID sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364.

First valid-image attempt reached 640 MiB, MemAvailable 86,596 KiB, but controls began after its 15-second hold ended; it is HOLD for control-plane survivability. Before repeat, post-target hold extended to 60 seconds. Allocation, VM ceiling (1024 MiB), per-container flags (768 MiB, 1 CPU), and control-operation deadline (15 seconds) are unchanged. No concurrent candidate. See issue #6669 comments for preregistration chronology.
