# Construction history
- construction-01: `STOP_SETUP_XAUTHORITY` before XTEST input. Private Xvfb and app started, but controller Python-Xlib searched `/opt/xvfb/.Xauthority`. No scientific inference. Pre-freeze correction: set controller-process `XAUTHORITY=/dev/null` only while opening the private `-ac -nolisten tcp` Xvfb connection.
- construction-02: four fresh schedules completed after the Xauthority correction. Independent raw audit with `--expected-reps 1` passed 4/4, errors=[]; all nine coherent copied-evidence mutations were rejected. This block is excluded from formal evidence.
