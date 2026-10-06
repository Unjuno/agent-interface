# Read-only checks

Use repository Git objects; no game, owner, model, harness, or frozen experiment is executed.

```
git merge-tree --write-tree cc5884ed802260b6236880e3b4ad2ea4abc8a4d8 21fecd58b9de30073c97234124e73b78c67d4b0c
git show -s --format='%H %T %P' 238bbb4a8e3ca8e2461cfefaa8c02e89b049b164
git merge-base --is-ancestor 6591b5703862c73d375a6646374ad82a26505bcb 238bbb4a8e3ca8e2461cfefaa8c02e89b049b164
git diff --name-status 21fecd58b9de30073c97234124e73b78c67d4b0c 50b4fb7b6870776d82a440a5bde67a737e779ac6
```

The merge-tree output must be exactly the recorded tree with exit 0. Compare every path/status with full-path-partition.json and every listed blob with `git ls-tree` or `git cat-file --batch`. For each closure-comparison entry, both prior and integration blob IDs must match the saved IDs. The partition describes the full pre-report content tree, while closure-comparison addresses reuse of the exercised dependency set; these are different checks.
