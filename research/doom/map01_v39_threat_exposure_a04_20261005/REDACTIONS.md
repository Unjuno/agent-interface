# Public archive redactions

The repository is public, so protocol-log copies in the published evidence bundles remove only persistent Codex installation/server/environment identifiers and account plan/rate-limit metadata. Model prompts, replies, turn identifiers, timing, and usage remain in the public logs.

The original A04 output and original ZIP are preserved locally at `C:\Users\user\Documents\Codex\2026-10-05\work\issue59-v39-live-a01\output\map01-v39-threat-currentmain-a04\`. The original unredacted ZIP SHA-256 is `67c1962a88fb9031d50b7599d5525c6b80e1ea7bab874f121941090bc58c7940`. The repository's sanitized `results/raw-a04.zip` SHA-256 is recorded in `AUDIT.json` and `PACKAGE_SHA256SUMS.txt`.

The sanitization changes only matching JSON fields in `planner-protocol.jsonl` copies and the derived archive/hash files. It does not change experiment events, screenshots, model content, or run outcome. The public protocol copy is therefore not byte-identical to the locally preserved raw protocol log; all study-relevant evidence is retained.
