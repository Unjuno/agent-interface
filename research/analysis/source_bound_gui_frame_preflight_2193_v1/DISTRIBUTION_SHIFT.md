# Distribution-shift result

The model was trained only on 8x8 positive squares and 64-point negative noise. Held-out accuracy on the reserved original distribution was 97.92%.

Positive acceptance under square-size shift: 4=80%, 6=95%, 8=92.5%, 10=87.5%, 12=82.5%.

Negative false-accept rate remained 0% for 32, 64, 96, 128, and 192 noise points in this limited fixture.

Conclusion: even this simple fixture loses recall under positive-shape shift. The model must not be promoted beyond its declared distribution; a real X11/container source needs shift tests and an unknown/yield path.
