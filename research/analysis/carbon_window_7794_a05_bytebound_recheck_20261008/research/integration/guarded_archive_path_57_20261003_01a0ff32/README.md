# Guarded archive-origin test repair

Parent #57; ordinary test portability repair by actual worker/session `01a0ff32-f520-79d2-b8cd-110e05130103` under FINAL-v5. Claim: #57 comment 5964842841. This restores the existing qualification entry on actual Windows.

## Change and result

`runtime/guarded_x11_v1/test_archive.py` adds `Path` to its isolated child and replaces two literal `archive + '/'` prefix assertions with `Path(module.__file__).is_relative_to(Path(archive))`. Component containment accepts actual Windows zipimport filenames and refuses neighboring archive names. Virtual zip members are compared lexically; no filesystem resolution is required.

On pinned base `6da2b492b9c2a9d76e5c54d35a0ae50b7b49edde`, the untouched existing archive test fails at its origin assertion after successful imports. The repair passes that test and all **76** guarded tests. `probe.py` extracts the repaired origin assertions, imports actual modules from the normal builder's archive under `python -I`, then runs **12** bounded path controls: actual/alternate separator/nested descendant accepted and sibling archive/adjacent prefix/external origin refused, for both bridge and compiled. The three non-actual paths per module are synthetic controls. `audit.py` separately checks retained child exits, paths and output with a literal component oracle; six effective corruptions are rejected, including Boolean/float exit aliases.

Actual platform: Windows, private Python 3.12.14, Pillow 12.3.0, python-xlib 0.33, six 1.17.0. No display, input, model, GPU, WSLc or formal allocation was used. These checks establish test portability and this finite origin boundary only; live X11, POSIX execution, task effects and timing remain unverified.

## Evidence and failures

`checks/` preserves each first command and child exit. `archive-base-red` is the initial setup failure (source export still incomplete, missing runtime import); `archive-base-red-ready` is the actual inherited assertion failure. Neither is presented as a successful check. The repaired test and controls subsequently pass. Worktree setup initially had an empty index; it was initialized from the full base tree before edits. A size-bearing Git enumeration caused unwanted historical blob hydration and was stopped; active runtime export then used tree metadata only and accepted existing executable file modes. These setup errors changed no repository source.

`path-controls/raw.json` retains all 12 child commands, timing records, exits and streams. `path-controls/build-manifest.json` pins the normal archive's **production source to the base commit**; the tested working-tree test SHA is in `MANIFEST.json`. The repair changes a test excluded from that archive; no production file was changed. The archive bytes are retained in the owned private output; SHA256 `99225099575489d8c74bef622bb07666287a944ae6cdadc19f351ba646ec29e1`.

Public evidence projects local paths and normalizes JSON/text newline formatting. Scientific raw fields are unchanged. `PROJECTIONS.json` records original/public hashes; original receipt stream hashes refer to retained private originals, not the projected public log bytes. `MANIFEST.json` hashes public bytes. Private originals were not rewritten. The initial public packaging diff check exposed CRLF as trailing whitespace; only generated public formatting was corrected. Existing #6900 evidence and its frozen head were untouched by this repair.

## Recheck and adoption

With the optional dependencies in the interpreter's own site packages (the child is isolated):

```sh
python -m unittest -v runtime.guarded_x11_v1.test_archive
python -m unittest discover -s runtime/guarded_x11_v1 -p 'test_*.py' -v
python <package>/audit.py <package>/path-controls/raw.json <new-audit-output>.json
```

Use a fresh destination when rerunning the ordinary `probe.py <repo> <new-output>` controls. No historical formal run should be repeated. Current main moved to `391789d9f7a1014e441cc360eaae9360ab034e85` during this repair and merged the sequence guard; the archive test itself is unchanged. These are pinned-base results, not an exact-current combined-tree confirmation. Content votes, applicable platform rules and a nonauthor exact-current combination confirmation remain required before any main write.
