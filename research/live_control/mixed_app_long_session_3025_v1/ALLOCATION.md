# #3025 repaired mixed-app geometry allocation

- Date: 2026-09-20 Asia/Tokyo
- Image: mixed-formal-3025:20260920
- Digest: sha256:c8fec4d7541b306b9266ce8d7800abad8e665e63d6ea1e5f62574d4b122a28d1
- Runtime: Debian bookworm-slim arm64; Xvfb :141; Openbox; Inkscape; LibreOffice Calc; Chromium
- Network: disabled; fresh container allocation.
- Outcome: STOP. Openbox enabled visible-window observations, but activation of Inkscape XID 4194312 timed out after 15 seconds.
- Model/network calls: 0/0.
- Gate: no PASS claim. Active-window control remains unavailable in this allocation.
- Source hashes: formal_session.py 253253b6afb393495c97871f4a503b8d174b07dda27f82b4166b363801794ddd; Dockerfile 963f32721bcc1e7657dc13bfb6ebad173ccce89eb068f92f69a32d3f54651f44; capture_run.py eb19a0a5e6760698e4194806c8044fef1b36d2ae3203316d1f4b818d52b24782.
