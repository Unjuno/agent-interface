# Native runtime backends

This directory contains platform-specific implementations/candidates behind the promoted platform-neutral runtime contract.

| Backend | Scope entry point |
|---|---|
| [`x11_v1/`](x11_v1/) | X11/XTEST integration candidate. |
| [`win32_v1/`](win32_v1/) | Win32 backend candidate using native Win32 APIs. |
| [`quartz_v1/`](quartz_v1/) | macOS Quartz/ApplicationServices backend candidate. |

A backend being present here does **not** by itself mean that the platform is generally supported. Read the backend's own README and retained evidence for its exact support envelope.

Shared admission, freshness, lease, and release semantics live outside this directory under [`../core_v1/`](../core_v1/) and the runtime kernel.
