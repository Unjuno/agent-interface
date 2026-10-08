# #6018 T0 A01 — Biased rare-fault exploration and valid likelihood-ratio estimation

**PASS_METHOD_SCOPED — finite authored IID synthetic model only.** The first formal 262,144 samples, frozen inputs and two process exit receipts are retained immutably in [bundle-a01.tar.xz](bundle-a01.tar.xz) and documented in [REPORT.md](REPORT.md). The archive has SHA-256 `6d65b164436dece48158ed9575cc339de072ee51f52f97c932fb2d8253c42798`.

- Owning [Issue #6018](https://github.com/Unjuno/agent-interface/issues/6018), [prospective source and decision freeze](https://github.com/Unjuno/agent-interface/issues/6018#issuecomment-6070911843), and related earlier [#5380](https://github.com/Unjuno/agent-interface/issues/5380). The old evidence remains unchanged.
- No Docker, WSLc, OrbStack, GPU, model, GUI, user data, real OS input or shared runtime was used in the experiment. Isolated Debian 13 Linux tool-container, CPython 3.13.5 standard library; no published container image digest. No deployed authority-safety or actual fault probability claim.
- `bundle-a01.tar.xz` includes byte-exact `spec.json`, `candidate.py`, `audit.py`, `formal/raw_candidate.json`, `formal/raw_audit.json`, console stdout/stderr/exit receipts, `SHA256SUMS.txt`, and construction-only data. **A01 has been consumed; do not re-run or overwrite its formal first outcome.**

Read and verify without executing:

```sh
sha256sum bundle-a01.tar.xz
mkdir -p a01-readonly && cd a01-readonly
tar -xJf ../bundle-a01.tar.xz
sha256sum -c SHA256SUMS.txt
```

Separate read-only audit reproduction must write to a new output path and not modify the retained formal raw. Any new formal experiment requires its own prospective identity, source freeze and ownership gate.
