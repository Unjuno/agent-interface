# A03 execution preflight

- Frozen main target: `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`.
- Host: macOS arm64; Python 3.14.5; 10 CPUs; OrbStack server 29.4.0.
- Host hardware memory: 64 GiB; at preflight, macOS reported 1,835,351 free 16 KiB pages (about 28 GiB). The OrbStack VM reported 16,808,173,568 bytes and 10 CPUs. `/private/tmp` volume had 211 GiB available. These are point-in-time readings, not isolation guarantees.
- Container preflight: `docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}'` failed before listing images with OrbStack/containerd content-blob error `sha256:c496fe61337ebef922bbd35d18f3a4d0f30c1524c0fc08fbcfff7b5c68d54643 ... operation not supported`. No image or container was started; no destructive store repair or repeat attempt was made.
- Selected bounded fallback: the standard-library finite model runs on this host under `/usr/bin/sandbox-exec -p '(version 1) (deny network*) (allow default)'`; this is host-only evidence, not container evidence.
- Before freeze, an isolated loopback socket attempt under the selected profile returned `PermissionError: [Errno 1] Operation not permitted` (exit 1); no network operation succeeded.
