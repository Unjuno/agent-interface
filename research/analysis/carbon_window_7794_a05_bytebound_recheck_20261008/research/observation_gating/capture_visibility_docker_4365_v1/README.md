# Pinned-Docker capture-visibility replication (#4827)

This is an environment-only revalidation of the scoped parent-region boundary from [#4365](https://github.com/Unjuno/agent-interface/issues/4365) / merged [PR #4385](https://github.com/Unjuno/agent-interface/pull/4385). It does not change or supersede the original result.

The experiment runs the exact merged capture adapter and pure assessor in a locally cached, immutable linux/amd64 Docker image, with fresh private Xvfb servers. It tests six coverage conditions twice, retaining exact window-client and root-screen XGetImage bytes. The independent auditor reconstructs the declared root pixels from geometry and checks source/raw hashes, visibility and cleanup. See [FREEZE.md](FREEZE.md) and [CONSTRUCTION.md](CONSTRUCTION.md).

No host desktop, user data, model/provider, GPU, input emission, network or runtime authority is involved. Even a scoped PASS is Docker/Xvfb reproducibility only.
