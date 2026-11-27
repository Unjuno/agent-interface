# Preregistration: current-main Calc same-frame Save integration, r86-c10

Date: 2026-11-03. One local Docker/Xvfb task attempt; no model or provider.
Source commit: `cf3ddf2f8ef44f78fac3cfed78df2904aa596691`.

## Question

Can the merged same-frame Calc Save effect verifier preserve a correlated Save
receipt and exact saved task effect through input release and natural app exit?
Pass gates are identical to r85: two verified enter/save releases; same digest
across final observations; correlated `effect_checked(status=unavailable)`;
one Save-request receipt with matching attempt/call/generation joins; pre/post
close verifier both prove A1=731/A2=864 and matching SHA-256; empty close-input
state, verified release, owner exit 0, natural Calc/oosplash/process-group exit;
Docker exit 0 and responsive Engine.

## Fixed conditions and one-shot rule

Unique ID `issue57-r86-c10`; one fresh task and one disposable container. No
retry. r84-c8 failed before GUI because its experiment script was absent from
the container evidence mount. r85-c9 also failed before GUI: root was read-only
and apt could not create `/var/lib/apt/lists/partial`. Both failures remain
separate and are neither pooled nor overwritten.

r86 preserves the r85 scientific task, source, image, packages, and resource
limits. Construction delta: mount tmpfs at `/var/lib/apt/lists` and
`/var/cache/apt/archives` to permit package setup while retaining read-only root;
/tmp remains tmpfs. The evidence directory is the only persistent writable
bind mount; source remains read-only. Image ID
`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`,
Docker 29.8.1, 2 CPUs, 4 GiB memory+swap, 256 PIDs, Debian mirrors for exact
packages `libreoffice-calc=4:7.4.7-1+deb12u14` and `tesseract-ocr=5.3.0-2`.
No model/provider/API calls, pull/build/prune, WSLc or MAP01. Xvfb :97,
1280x800x24; OCR guard skip; fixed public Calc profile and exact saved task.
Task timeout 600 seconds. No speed or cross-domain claims.

Preserve all raw evidence and failures. Any missing gate is FAIL/UNKNOWN.
