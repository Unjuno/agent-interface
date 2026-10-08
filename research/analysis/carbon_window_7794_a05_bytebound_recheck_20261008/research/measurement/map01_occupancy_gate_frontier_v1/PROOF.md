# Exact gate-native derivation

Let refined gate-native fields be `W' = W-dW` and `U' = U-dU`, with `U'>0`, and threshold `q=a/b`, `0<a<b`.

The frozen gate is

`W'/U' <= a/b`.

Because `b>0` and `U'>0`, cross multiplication preserves order:

`b(W-dW) <= a(U-dU)`

`bW - b dW <= aU - a dU`

`b dW - a dU >= bW - aU`.

Thus the frontier and direct ratio gate are exactly equivalent for every valid gate-native refined pair. This proof deliberately does not substitute independently rounded `lower` into `W=U-L`.

For retained v39, `W=2,151,534 us`, `U=8,452,733 us`, `a=1`, `b=4`:

`D=4W-U=153,403 us`.

With fixed upper (`dU=0`), minimum integer `dW=ceil(D/4)=38,351 us`.

With lower fixed, upper inward motion `x` implies `dW=dU=x`; hence `3x>=D`, so `x=ceil(D/3)=51,135 us`.
