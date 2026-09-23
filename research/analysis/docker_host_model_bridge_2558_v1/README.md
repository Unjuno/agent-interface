# Docker-to-host model bridge (#2558)

The Docker/native observation image is passed through a narrow file boundary
to the PC-local `codex.exe` model runner. The bridge returns the existing
compiled grounding contract and records model usage plus image provenance.

The bridge is intentionally non-authoritative: it never emits input, and the
next runtime gate must independently validate focus, geometry, pixel change,
and scored effect.
