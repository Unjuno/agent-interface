# Native Windows client-pixel hash

The controlled Tk fixture was launched twice and its exact client rectangle was captured with Windows GDI `BitBlt` + `GetDIBits`; no screenshot payload was uploaded or decoded.

- target_present=true: 320x240, 240 scanlines, 307200 bytes, SHA-256 `ea72d1865886bedbe699f10e9d63a51fbc837b73e55887e20bf376378ecee10b`
- target_present=false: 320x240, 240 scanlines, 307200 bytes, SHA-256 `aa86fbcb2dca06faec0a761e62aef80b06edc914f012b66cce61f9dd9cfe0305`

Hashes differ and both captures have complete dimensions/scanlines. This establishes native pixel-byte observation bound to controlled fixture state, not model accuracy or gameplay transfer.
