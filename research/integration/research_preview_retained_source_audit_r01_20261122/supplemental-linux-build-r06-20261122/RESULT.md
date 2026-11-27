# Supplemental R06: supported WSL package build

Status: PASS_PACKAGE_BUILD_AND_EXTRACTED_RETAINED_AUDIT.

- Frozen candidate: `6c50fdce0d857fbf1a7c647bcd6ca9a17f8c05c0`; base main: `128c33f22a042b83a51351debdc32ef3ae5bfa4b`.
- Ubuntu WSL 2 Linux host, clean detached candidate checkout; existing local Git object stores were reused with `GIT_NO_LAZY_FETCH=1`, so no new object download was needed.
- Builder exit 0 in 24.43 s. It selected 22,646 files, included 30 frozen-source archive members (manifest + 29 files), validated exact closure and launcher modes, and passed checkout and extracted-archive launcher preflight.
- Artifact: `/home/user/agent-interface-preview-output-r06/agent-interface-research-preview-2026-09-17+6c50fdce0d85.tar.gz`; 349,878,418 bytes; SHA-256 `73147dc192c7b472a47a4730b7886fe297beb75182cad2f677b368232ae38ef8`.
- Extracted artifact retained audit exited 0: 29/29 frozen files matched, no archive mismatches, seven later source-content differences were reported, disposition `RETAIN`.
- Raw builder stdout, stderr, exit, conditions, result, artifact manifest/SHA list, extracted audit stdout/stderr/exit, and artifact location/hash are preserved here. The 350 MB artifact remains outside Git in WSL output storage.
- Offline packaging/audit only. No live allocation, model call, GUI, input, task action, dependency install, or publication.

The Windows build attempt is a separate host-boundary STOP (the builder correctly rejected the non-POSIX launcher environment); the supported WSL build above is the successful product-target build.
