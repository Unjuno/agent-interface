# v5 excluded construction seed (non-formal)

Allocation: `needle-role-skill-joint-retention-20260928-v5`; image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e` (`linux/amd64`).

- Stage 0: networkless Docker, read-only source/root, 0.25 CPU; 13/13 tests passed in 0.161s.
- Stage 1: exactly one excluded construction seed `9970014`, networkless Docker, read-only source, 1 CPU; launcher exit 0; exactly one raw JSON produced (538,352 bytes); no formal seed consumed; no retry.
- Independent audit: separate networkless container, read-only raw mount; `PASS_CONSTRUCTION_AUDIT`, zero errors.
- Raw SHA-256: `cc9208e3ce726896d9d0f426aa1971cb3cb8e737ef06553f6392b613bd3ecdb7`.
- Replayed descriptive scores (non-formal): routed separate skills A=1/B=1; routed shared adapter A=0/B=1; shared-A replay A=0.41796875/B=0.94921875; shared-B-only A=0/B=1.
- Stage 0 stdout SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; stderr: `a73223dc3e6a3e5cde fd4ca9efe3636f8e5f8e4f056c19655bf7f2466b27b6e5` (digest is `a73223dc3e6a3e5cdefd4ca9efe3636f8e5f8e4f056c19655bf7f2466b27b6e5`).
- Launcher stdout/stderr SHA-256: `71ab55792a6d10df6d79559724bcf7b47efcb1a8a051f748c834e48f84da109a` / `72a2cda6558c65d05be67c2df113ba61e02c974ecf3a1cfeda9013e8f4937c03`.
- Audit report SHA-256: `69fae3c73cd627f93484f63a06f7edb6f7c29c2d1f02f495e4c07b957c8928da`; audit stdout/stderr: `955d97601cb00c1959536f5563a5aeec19101d7cea634490b95bf07e21b2d1fe` / `11733f363ac18ba36750cdc8cda835000fb755598d942bc0727ebb2fa997f9c3`.

This is only a construction/protocol check on an excluded seed. It does not establish learning effects or generalization. All three preregistered formal seeds remain unspent. Exact raw and transcripts are preserved in the local execution workspace; this GitHub report publishes their hashes and summary, not the 538 KB raw payload.
