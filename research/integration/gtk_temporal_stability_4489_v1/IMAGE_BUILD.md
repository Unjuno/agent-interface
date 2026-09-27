# Frozen image provenance

The formal image was created locally with OrbStack's Docker-compatible CLI; it was not pulled from a registry and no Dockerfile build is claimed.

1. Create `issue4466-formal-stage-01-20260926` from base image `sha256:296d358f5c71e6c3e766c49ebfe13b9b1ec5c2837157da2cfe406ee73bfb2992`.
2. Copy the frozen experiment directory into `/experiment` in that named staging container.
3. Commit the staging container as `issue4466-gtk-pixel-stability:formal01-20260926`.
4. Resolve the tag to immutable image `sha256:7c202113e519666007d7f6a74fa4a9854ed7cec62c07c1e80631474e69af7a27`, platform `linux/arm64`; verify the eight runtime-file hashes against `FREEZE.json` inside that image.
5. Run the one formal command recorded verbatim in `FREEZE.json`.

The intermediate staging container id was `2c75cfe9989c4f50859a9c28f89ef72896f613283239e41483bd756e19b7fc9b`. The base image is itself derived from the pinned GTK/Xvfb image and the pinned xwd donor documented in `FREEZE.json`. BuildKit local-image metadata resolution returned HTTP 502 during construction, so this deterministic local container-stage/copy/commit procedure was used instead. The formal image and formal container were inspected after execution; the formal container exited 0 with `--network none` and a read-only root filesystem.
