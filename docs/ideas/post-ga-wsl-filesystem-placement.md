# WSL filesystem placement after WSLc general availability

- **Status:** Unverified placement question; environment checks crossed the Issue's shared-lane gate.
- **Source:** Issue [#7970](https://github.com/Unjuno/agent-interface/issues/7970), successor to [#3503](https://github.com/Unjuno/agent-interface/issues/3503).
- **Idea:** Re-test whether active research artifacts should live on the Linux-side or Windows-side filesystem under post-GA WSLc, using repository-relevant workloads rather than extrapolating Microsoft's headline claims.
- **Outcome:** No placement experiment or scientific result is recorded. An image-listing call and later version/system-info calls were made before explicit owner reconciliation; no image was pulled/built/deleted, no container was started/stopped, and no candidate/auditor ran. Ownership and cached-image state remain UNKNOWN. The gate applies to this Issue's WSLc lane only; it does not stop independent repository work.
