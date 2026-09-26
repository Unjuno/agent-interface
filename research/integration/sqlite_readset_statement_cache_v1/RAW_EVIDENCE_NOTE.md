# Raw evidence reconstruction

The full original raw evidence archive is retained as a standard Git binary patch in `EVIDENCE.binary.patch`.

It reconstructs exactly:

- path: `research/integration/sqlite_readset_statement_cache_v1/EVIDENCE.tar.xz`
- bytes: **182,848**
- SHA-256: `176edb7eff101dfc1db2c3eef3ae90382f446db1804a3a34bb96f6105199d86b`

Review from a fresh scratch repository:

```sh
mkdir /tmp/sqlite-readset-4088 && cd /tmp/sqlite-readset-4088
git init -q
git apply --binary /path/to/EVIDENCE.binary.patch
sha256sum research/integration/sqlite_readset_statement_cache_v1/EVIDENCE.tar.xz
```

The expected digest is the value above. The directly published `CAPSULE.json` binds the archive's **2,579 original members** and `restore.py` verifies/extracts the archive into a new destination.

The binary patch is transport only. Applying it is not a formal experiment rerun. Do not run the consumed formal allocation again merely to review retained evidence.
