# Native X11 tight-loop text pacing v1

Experimental fork of frozen native-X11 source `ca141254c949f7ce42f9967f752a517ff521421b` (base backend Git blob `ed8186b277afc81f43e0119d78b1d5fdbc601f6e`) inside a new namespace. Existing `research/runtime_native_x11_v0/**` remains unchanged and capability-honest.

This candidate adds only strict lowercase-ASCII `text` execution inside the same compiled Go+cgo/XTest `Execute` loop, configurable pacing, and timing receipts. It is not a generic text/IME implementation and does not promote the original backend's manifest.
