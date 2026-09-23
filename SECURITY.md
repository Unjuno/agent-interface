# Security and safety

This repository contains experimental computer-control harnesses that may inject real keyboard and pointer input into an X11 desktop.

## Research-code boundary

The current code is not an authorization or sandboxing system. A valid control sequence can still activate destructive UI actions if aimed at the wrong application or environment.

Run the GUI experiments only in an isolated desktop/X server/container with disposable state.

## Reporting security-sensitive problems

Do not publish credentials, private screenshots, access tokens, or other secrets in a public issue. If a finding requires sensitive reproduction material, reduce it to a non-sensitive minimal case before filing publicly.
