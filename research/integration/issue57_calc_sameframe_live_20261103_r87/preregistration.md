# Preregistration: current-main Calc same-frame Save integration, r87-c11

Date: 2026-11-03. One local Docker/Xvfb task attempt; no model/provider.
Source commit: `cf3ddf2f8ef44f78fac3cfed78df2904aa596691`.

Question/pass gates unchanged from r84-r86: verify the enter/save input-release
receipts, unchanged final observation digest plus correlated
`effect_checked(status=unavailable)`, one correctly joined Save-request receipt,
exact A1=731/A2=864 verified before and after close with identical artifact
SHA-256, empty close input state, clean natural Calc/oosplash/process-group exit,
and responsive Docker Engine with container exit 0.

## Frozen conditions and one-shot rule

Unique ID `issue57-r87-c11`; one fresh task/container, no retry. Earlier
constructions remain separate failures: r84 omitted the experiment script from
the evidence mount; r85 used read-only root and apt could not create its list
partial directory; r86 made apt list/cache writable but dpkg could not update
`/var/lib/dpkg` on read-only root. None launched Calc, none is pooled or
replaced.

r87 preserves source/task/image/packages/limits and fixes construction by
allowing writes in the disposable container root filesystem. Persistent binds
remain source read-only and attempt evidence only. Container is removed after
run (`--rm`); raw evidence persists in the attempt directory. Image ID
`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`,
Docker 29.8.1, 2 CPUs, 4 GiB memory+swap, 256 PIDs. Exact Debian packages are
installed from configured mirrors. No provider/model/API calls, image
pull/build/prune, host setting change, WSLc or MAP01. Xvfb :97 1280x800x24;
OCR guard skip, public Calc profile, task timeout 600 seconds. No efficiency
claim. Missing gates are FAIL/UNKNOWN.
