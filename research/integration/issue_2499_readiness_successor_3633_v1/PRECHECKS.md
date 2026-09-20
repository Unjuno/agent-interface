# Construction and pre-formal checks

- GitHub default branch: `main`; frozen base commit `5db7858067bda50590674370f494230f2a5dd6d9`.
- Container engine: OrbStack Docker, linux/arm64.
- Pinned local image: `mixed-app-identity-2782-local:latest`,
  `sha256:e6ced3789130dae21c7b42b7b9d25cd590a271a77910e16c01d2edf87e44cee6`.
- Image application versions: Inkscape 1.2.2, LibreOffice 7.4.7.2,
  Chromium 153.0.8010.47, Python 3.11.2. Xvfb and xdotool are present.
- Construction-only invocation: existing image entrypoint, no mounts,
  `--network none --read-only --tmpfs /tmp:rw,nosuid,size=512m --shm-size=512m`.
  Exit 0, decision `PASS_IDENTITY_DISCOVERY_SCOPED`, four windows found across
  the three apps, stable first/second snapshots, distinct app identities,
  zero input/model/network. Raw CLI output is retained in the preregistration.
  The extra Calc Tip-of-the-Day candidate was visible and is excluded by the
  preregistered Calc main-window title filter.
- Typed identity unit suite in the same pinned image, source mounted read-only,
  network disabled: `python3 -m unittest
  research.integration.mixed_app_identity_2666.test_identity_gate`; exit 0,
  4 tests passed.
- No formal allocation has run at the time of this precheck record.
