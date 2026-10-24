# Construction failure A00 — WSL Git pointer

The first native Ubuntu WSL freeze attempt exited 1 before writing `FREEZE.json`. `git rev-parse HEAD` could not follow the worktree `.git` pointer, which contains a Windows absolute path (`D:/...`); Git interpreted the path as `/mnt/d/.../D:/...` and returned `fatal: not a git repository`.

This is an environment/path construction failure, not an audit or allocation result. The checkout HEAD and Git-derived merge file list were read on Windows and frozen as audit inputs. Subsequent data reads and candidate/verifier runs used native Ubuntu WSL Python without invoking Git.
