# Window identity successor for #2499

This path isolates the window-discovery failure retained in #2499/#2658. It
must not be interpreted as a mixed-app session result. The resolver uses
visible-window enumeration plus `xprop` `_NET_WM_PID`/`WM_CLASS`/`WM_NAME`
properties, accepts exactly one matching surface per application, and refuses
missing or ambiguous matches. It performs no model or task input.
