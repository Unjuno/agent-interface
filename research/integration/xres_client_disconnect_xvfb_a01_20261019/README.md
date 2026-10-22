# XRes client-disconnect / queued-key probe A01

**Outcome:** `NOT_ESTABLISHED` (first trial stopped; no safety PASS claimed).

A single fresh WSLc allocation ran against a digest-pinned cached Python 3.12.3 image. Xvfb was stopped after the owner connected. The owner wrote a flushed XTest KeyPress and blocked in `XSync`; a separate preconnected client issued XRes `QueryClients`, also blocked, and the parent retired that helper in 1.114 ms. The owner was then killed in 1.087 ms. After Xvfb resumed, the exact owner base disappeared from XRes within 0.932 ms. However, the keymap showed the key was **not down** at that point, so the intended server-side queued-DOWN condition was not established. The probe stopped on its first trial and did not attempt an UP because no held key was observed.

This is a construction failure for the queued-DOWN scenario, not a release failure and not evidence that the helper is a release fence. The request had been flushed by Python-Xlib while Xvfb was stopped, but the outcome cannot distinguish whether the server never read it or discarded it when the owner connection died. `QueryClients` absence only showed that the client had disconnected in this run. No task effect was tested.

## Frozen conditions and evidence

- Source commit: `5f35c41f6b1c1afa11326c698dc782cc7830dfbd`; branch `runtime/guarded-mcp-owned-process-20261018`.
- Probe SHA-256: `b6be4e38101d182797a289b711106e84a5b0de3e4309bdf52488babce1f0cf39`.
- Production helper SHA-256: `f6c9bad600bc0575400a937ab98336f9c5ef57b29dfbd5a3943089d75c19c6d2`.
- Runtime: WSLc 3.0.3.0; cached `python@sha256:fd3817f3a855f6c2ada16ac9468e5ee93e361005bd226fd5a5ee1a504e038c84` (`linux/amd64`, Python 3.12.3); pull policy `never`; source mounted read-only.
- Dependencies installed inside this one disposable container over WSLc `bridge`: Debian 12; `xvfb`/`xserver-common` `2:21.1.7-3+deb12u13`; `python-xlib==0.33`; `six==1.17.0`. The run was not network-isolated; the container was removed automatically.
- Raw stdout/stderr: [`raw/wslc-run-raw.log.gz`](raw/wslc-run-raw.log.gz), SHA-256 `a0f6085e7a0064057b37db5bb242c2a4dd39989a764e5189ca0f3cbd26505251`.
- Conditions: [`conditions.json`](conditions.json). Run receipt: [`run-result.json`](run-result.json). The exact container ID is retained in [`raw/container.cid`](raw/container.cid); an exact-ID WSLc lookup after exit returned no container.

## Scope and next step

This is Xvfb-only. It says nothing about a physical desktop, XWayland, a GUI application, or release while the X server remains unavailable. The next distinct experiment should establish an independent recipient's KeyPress event while the owner waits on a deliberately withheld X reply, then kill the owner, confirm exact-client disappearance, send UP from an independent connection, and verify both the recipient's KeyRelease and keymap. That tests blocked owner I/O only while the server can still process independent cleanup; it still cannot establish a bound under permanent server nonresponse.
