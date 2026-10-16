# A01 construction stop

Disposition: `STOP_INFRASTRUCTURE_PRE_CANDIDATE`.

The isolated WSLc container started with the frozen image and network disabled, but the mounted Windows worktree's `.git` file refers to a host path that does not exist inside the container (`/src/C:/...`). The candidate stopped during its repository-commit lookup before loading the V39 loop or running any case. Exit code: 1. Candidate stdout was empty; the retained local stderr SHA-256 is `c186069084bef36588755b9437a24ea86dac73cea194b8ee5ab6c3bd01b53bba`. The public receipt redacts the host path. Independent audit was not run because no candidate result existed.

The experiment was not retried under A01. A02 moves the Git commit check to the Windows runner and leaves the container source mount read-only. A02 has a distinct freeze and output path.
