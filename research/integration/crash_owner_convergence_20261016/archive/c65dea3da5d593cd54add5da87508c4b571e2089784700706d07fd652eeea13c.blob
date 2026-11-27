# Freeze errata

The network_during_test field in FREEZE.json says “disabled by no network namespace available”. That wording is inaccurate: no network namespace isolation was configured, so network access was not forcibly disabled. The candidate code path itself uses only local files, Python modules, and Xvfb, and makes no network calls. Package installation and apt operations occurred before the candidate run. Preserve the original freeze unchanged; interpret this limitation as no network isolation, not as a network-disabled sandbox.
