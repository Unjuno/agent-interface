# Reproduction correction for V15 per-key owner evidence (#8102)

This note corrects only the source-fetch check in the original package README. The frozen candidate, retained runs, audit outputs, and their checksums are unchanged.

## Issue

The original instructions fetch the mutable `refs/pull/8065/head` and then require `FETCH_HEAD` to equal frozen candidate commit `4158d9b063e7cbf56828f1b0667ec2714af0ff2b`. PR #8065 has advanced, so `FETCH_HEAD` is now its newer tip and that equality check stops before the audit. The audit itself reads the frozen object by its fixed SHA using `git show`.

At this correction's review, GitHub reported current PR #8065 head `6591b5703862c73d375a6646374ad82a26505bcb`; comparing it with the frozen SHA showed the frozen commit is an ancestor, two commits behind. Fetching the current PR ref therefore makes the frozen object available without treating the newer tip as the experiment source.

## Corrected retrieval check

Run these read-only Git checks from the root of a clone of this repository:

```sh
git fetch --no-tags origin refs/pull/8065/head
git cat-file -e '4158d9b063e7cbf56828f1b0667ec2714af0ff2b^{commit}'
git merge-base --is-ancestor 4158d9b063e7cbf56828f1b0667ec2714af0ff2b FETCH_HEAD
```

The object-existence and ancestry checks ensure the fetched history contains the exact frozen commit. They do not run the candidate or auditor. The original `audit.py` writes `results/AUDIT.json`, and `replay_startup.py` launches the three retained startup routes into a new output directory; neither is part of fixing this retrieval instruction. The already-retained candidate and audit results remain the evidence for this correction. Any future probe or audit run should be separately versioned and write to a new result path. The auditor remains pinned to the frozen SHA; do not replace it with the current PR head. If either check fails after a ref update or history rewrite, stop and recover the frozen commit rather than changing the expected SHA.

This is a documentation correction only. It does not change the source-selection result or its limits. No candidate, auditor, game, model, GUI, X11, or OS-input run was executed for this correction.
