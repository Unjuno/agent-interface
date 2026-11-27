# Conditions — current-main WSL Research Preview bundle R02

- Remote `refs/heads/main` returned `c5fc0ee00b5fa5208088ee69004a336770336ac4` before the shallow clone.
- Ubuntu 24.04 WSL, Python 3.12.3, Git 2.43.0. Clone/worktree stored under persistent `/home/user`, not `/tmp`; complete checkout and sparse checkout disabled only in this new worktree.
- Source was clean at the frozen commit. Twenty-nine frozen archive entries were hash-checked before building.
- Commands:
  - `python3 release/preview_bundle_v1/test_build_preview.py -v`
  - `python3 release/preview_bundle_v1/build_preview.py --root <checkout> --out <output>`
  - Extract built tarball; run packaged `runtime/golden-demo-v3.sh audit-retained`.
  - `sha256sum -c SHA256SUMS` in output directory.
- No dependency installation, doctor, live Golden run, `audit-live`, model, GUI or live input.
