# User-facing releases

GitHub Releases are intended for artifacts a user can actually download and try.

The repository itself remains research-first. Historical `v0.0.1-research.*` prereleases are archival research snapshots and are not the target release format going forward.

## Runtime preview gate

A user-facing preview should include:

- a runnable package or executable archive;
- checksums;
- a minimal quickstart;
- supported operating systems/backends;
- known limitations;
- a small smoke test or self-check;
- a link to the benchmark evidence supporting the promoted runtime behavior.

The release should not require reading the research tree to discover how to start it.

## Release tracks

- **Research repository:** experiments and evidence on `main`.
- **Runtime preview releases:** downloadable, runnable distributions for users.
- **Stable releases:** only after execution semantics, recovery behavior, installation, and cross-app correctness are substantially frozen.

## Principle

A release is not just a tagged research snapshot. It is a usable artifact with an explicit support envelope.
