# A01 setup STOP (no candidate process)

The command used the local image configuration ID as though it were the image RepoDigest. WSLc returned `WSLC_E_IMAGE_NOT_FOUND` before creating a container process. `run_candidate.py` did not execute and no candidate raw output was produced. This setup STOP is excluded from the A02 result.

The frozen hash for A01 runner was `acb293156336f9d864b42ae95f30950c2666fc9717a3fc6dff629cd55e26bdd5`. After the STOP, source editing replaced the working copy; the exact A01 runner bytes were not preserved. The failure's cause is independently explained by `wslc inspect`: image config ID `sha256:414a...` has RepoDigest `python@sha256:dddf...`. This is a provenance limitation of A01 only; A02 has its exact source and hash-bound freeze.
