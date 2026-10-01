# Immutable GTK fixture image successor (#2748)

This path addresses only the missing `gi` dependency diagnosed in #2741. The
Dockerfile uses the local immutable Python base digest
`sha256:e635facd4cd70a0e0b5d72cb0ce38f24434b6e98e11c2383d428a880c0f7232c`,
installs Debian `python3-gi`/GTK3/Xvfb packages, and exposes the Debian package
path to the container Python. It does not claim formal #2606 acceptance.

## Local readiness result

Built locally as `agent-interface-gtk-fixture-v2:2748` from image digest
`sha256:65c35be50f37bca68c35f514e62dc1a16daf75f5b6b663bab349ea928667a739`.
The Dockerfile SHA-256 is
`c5c3c41ec388996b94974618ebf5c2df4fb71b45732637cbfbb585447b145117`; the
exact main fixture source SHA-256 is
`2f8ed8c604afbcf5dd43363d2ede4950e70aa9f7eae70a4b795decf4feb4bb3b`.

Under private Xvfb `:145`, `import gi`/GTK3 succeeded and the exact fixture
emitted `{"toolkit":"gtk3","window_id":2097155}`. It remained alive until
the bounded 8-second readiness timeout and was then terminated cleanly. Decision:
`PASS_GTK_FIXTURE_READY_IMMUTABLE`; input/model/provider/network calls were 0.
This only unlocks a separately frozen matrix allocation; it is not #2606
acceptance.
