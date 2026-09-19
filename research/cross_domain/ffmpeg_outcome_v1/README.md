# Real FFmpeg outcome transfer

Issue #232. Research evidence only; no shared-runtime integration. Read REPORT.md for findings and limits.

The three numbered files are BINARY consecutive chunks of one XZ tar, not base64 text. They retain all six exact executed/tested Python sources, full frozen plan, environment, expected artifact predicate and full per-case result. Reconstruct outside this repository directory and extract into an EMPTY independent workspace:

```sh
cat source.tar.xz.parts/000 source.tar.xz.parts/001 source.tar.xz.parts/002 > /tmp/ffmpeg-outcome-source.tar.xz
printf '%s  %s\n' ec451d28fe06aabc531e892548fa1829e2d2d9875cace799ce337e3efc6b4337 /tmp/ffmpeg-outcome-source.tar.xz | sha256sum -c -
mkdir /tmp/ffmpeg-outcome-replay
cd /tmp/ffmpeg-outcome-replay
tar -xf /tmp/ffmpeg-outcome-source.tar.xz
python -m unittest discover -s research/cross_domain/ffmpeg_outcome_v1 -p test_contract.py -v
```

The 24 contract/PNG tests need Pillow. The other 13 audit-mutation tests need the retained raw preflight. Full offline replay requires the separately delivered raw evidence archive, whose digest is in VALIDATION.json. The raw archive has the same independent-workspace layout and includes all commands, stop logs, outputs, screenshots, fixtures and setup failures. It does NOT contain font files or installed binaries.

From a full evidence workspace: `python research/cross_domain/ffmpeg_outcome_v1/audit.py . --out replay.json` (standard library only); then `python -m unittest discover -s research/cross_domain/ffmpeg_outcome_v1 -v` (37 tests).

Do not run Python with -O because the research auditor uses assertions. Do not rerun consumed IDs or overwrite a checkout. New live runs require a new output root, relocated absolute command paths, a new source/plan freeze and matching executable/library environment. This harness uses private xterm/Xvfb/XTEST, NOT production Executor/InputOwner. No result grants retry/input authority.
