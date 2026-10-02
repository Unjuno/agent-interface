# Allocation 12 construction record (WSLc, CPU only)

Captured 2026-10-02 UTC before any formal candidate, CUDA timing, or raw auditor.

- Image: `pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`, cached image ID `sha256:048a0de5d4322054f9d92a9dfd36f4cab1cd82dfbd1042ce2c51bd94f7e45d32`.
- WSLc reported: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` This is retained as a warning; no effective memory/swap limit is inferred.
- One CPU-only WSLc invocation generated the new seed-49720261012 dataset; exit 0, 1,024 rows.
- CPU-only construction tests: dataset contract 3/3 PASS; full raw-auditor mutation controls 8/8 PASS (six result, two source); unsafe-admission helper 3/3 PASS.
- No GPU flag was used during construction. No candidate, formal CUDA timing, or formal raw auditor has run; formal counts are 0/0/0, retries 0.
- A preliminary source staging attempt failed before the frozen package was made because the Windows transfer encoded UTF-16 byte order incorrectly; Python reported an invalid character. The source was rewritten with UTF-8-compatible conversion and all stated construction checks then passed. That scratch failure is not a candidate attempt and produced no formal output.
