# Current-main reconciliation — 2026-10-05

This note records the rescue delivery against current main. The historical A01/A02 reports, raw outputs, source snapshots, fixtures, and SHA-256 manifests remain unchanged.

- Current main at this reconciliation: `dbeb50b756bb0d77547b0e7f4de50e6d633c857d`.
- The 13 experiment-package files remain absent from that main tree and are carried by their existing Git blob IDs. All 10 entries in the two package manifests match their recorded SHA-256 and byte count; each pinned source snapshot matches its original source commit's Git blob.
- The rescue branch is synchronized with current main by a merge commit. The repository index links both reports. The current file-path comparison with #8065's head `6591b5703862c73d375a6646374ad82a26505bcb` has no overlap with the 13 rescue-package paths. This does not resolve #8065 or imply approval.
- PR #8140 remains closed unmerged because its stale-base comparison exceeded GitHub's 300-file diff limit. Its branch and history remain retained as provenance; this PR is the clean-base delivery path.
- No candidate or auditor was rerun during packaging. Results remain synthetic and source/fixture bounded; no live input, physical key, game, application effect, or task benefit is claimed.


## Latest synchronization — 2026-10-05

Rescue branch refreshed against current main `fd4f9e4533aa5baa5952e89cd830c98b26e7c537`. The 13 evidence package blobs are unchanged; only the index and reconciliation note are refreshed.


## Latest synchronization — 2026-10-05

Rescue branch refreshed against current main `21fecd58b9de30073c97234124e73b78c67d4b0c`. The 13 source-pinned evidence package blobs remain unchanged; only the index and reconciliation note are refreshed.
