# Retained setup / harness outcomes

- Unscored stable calibration: identified the historical XLSX modal title exactly as `Confirm File Format`; not part of the scored pair.
- `c254-pair-01`: **HARNESS FAIL, 0 scored arms**. Private Xvfb/Openbox/LibreOffice launched, but the parent runner did not propagate its own `DISPLAY`/`XAUTHORITY` before python-xlib window enumeration. Xlib attempted `/opt/xvfb/.Xauthority` and raised `XauthError` before Calc window discovery/precheck/input. Cleanup terminated private processes. No scientific result was inferred.
- `c254-pair-02`: changed only parent environment propagation plus versioned output/allocation names. First complete scored pair retained; no rows from pair-01 are pooled.
