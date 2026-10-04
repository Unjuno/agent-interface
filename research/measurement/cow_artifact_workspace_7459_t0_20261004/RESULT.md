# Formal result — Issue #7459 T0

**Disposition: `HOLD_NO_CONSISTENCY_OR_EFFECT_ORACLE`**. The frozen candidate ran once and exited 0, but the independent auditor returned `FAIL_AUDIT`. The original audit result is preserved unchanged at `raw/audit.json`; no candidate or audit rerun was performed.

## What happened

- Two clean artifact cases (single-file edit; multi-file edit/create/rename/delete) produced the expected file bytes. Docker's writable layer retained the edits and `docker diff` reported the expected `/workspace` changes.
- The metadata case preserved the requested mode change (`single.txt` 0644 → 0600).
- The interrupted-save case wrote only `alpha.txt`, exited 23, and was refused. Dirty/open-buffer and changed-base-revision cases were refused before container creation; these states are not inferable from fixture bytes alone.
- The attempted network request exited 1 under `NetworkMode=none`. All cases had private IPC, no bind mounts, and bounded PID count.
- The direct-live disposable control changed its base; the private-copy draft control left its base unchanged and retained the exact changed draft.
- The independent auditor rejected all four planted corruptions (delta entry, exported hash, false acceptance of a refused case, and removed network-denial evidence).

## Why this is not a method PASS

In every container, `docker diff` also reported changes under `/etc/ssl` and `/usr/local/share/ca-certificates`, including `orbstack-root.crt`. These changes were outside the artifact subtree and were captured in raw output, but their provenance and meaning were not in the frozen effect allowlist. The candidate accepted clean work based on its planned artifact action; the auditor correctly rejected whole-layer equality because observed container effects exceeded that plan. The path names suggest OrbStack CA injection, but this experiment did not establish that attribution independently.

Thus the experiment demonstrates that Docker-managed COW can retain the tested bytes, not that the full COW layer is a clean or application-consistent GUI draft. Under the frozen gate, the unplanned layer changes leave effect attribution unresolved. The original formal auditor status remains `FAIL_AUDIT`; the research conclusion is HOLD, not PASS or a hypothesis-wide FAIL. The earlier nested OverlayFS mount `Invalid argument` is a separate setup result and is not combined with this candidate.

## Provenance and raw evidence

- Frozen main: `93090bcbf0c9eb0cd5f6feeb4abd2477e8453202`.
- OrbStack Docker: client/server `29.5.2/29.4.0`; engine `linux/aarch64 overlayfs`.
- Base image: `alpine@sha256:5291449c3df73caf6ed85e649dec1b9e818b39a5d8c871e97afc13e9cd5e8fa8`.
- Freeze SHA-256: `9d6b391997d41fa3745ea5a85b5435b7f87de86a628053de185d5e0e1f6cdd84`.
- Candidate SHA-256: `b8b2a260698eb19883f5df501f416e039ccb362214a2d750f364f94d324288e5`.
- Independent auditor SHA-256: `b1d0f29ec3d7be2483a5b726ab7ac31830602c0f4393dd469e818ad1b5e6cfc7`.
- Raw candidate SHA-256: `2efa5b34e82e18220448e2768268e808c922dcbd0397f167372d7e2d2c82bcb7`.
- Original audit SHA-256: `52778f966b47409fd2546037e0b6ec73bce0cb6e3c3f4d94260b885f545295e6`.

No user files, host artifact paths, or pre-existing containers were modified. All run containers were removed by the candidate; the locally built experiment image was retained. No external network endpoint was contacted successfully.

## Scope and next boundary

This is one synthetic file fixture on one OrbStack engine. No real application, GUI, open buffer, plugin, host APFS snapshot, human review, user promotion, or general isolation boundary was tested. Do not repeat the frozen candidate. A genuinely new experiment would first need a prospective, independently justified policy for separating runtime-provided container mutations from task deltas, then a new source/image freeze and distinct allocation; otherwise prefer native drafts or sequential interaction.

## Local repository checks

- `python3 -B -m unittest discover -s research/analysis -p 'test_analysis_checkout.py' -v` — PASS, 3/3.
- `python3 research/analysis/check_index.py` — PASS, 669 retained result/failure directories indexed.
- Python AST parse for the three package scripts — PASS.
- After syncing the branch to current `origin/main` (`fb2951c5514685028ea6a77805ee084a794e3110`), the same 3/3 checkout tests, 669-entry analysis index, three-script AST parse, and full `git diff --cached --check` all passed.
- The formal `python3 audit.py` result is intentionally recorded separately above as `FAIL_AUDIT`; repository CI passing does not convert the scientific disposition.
