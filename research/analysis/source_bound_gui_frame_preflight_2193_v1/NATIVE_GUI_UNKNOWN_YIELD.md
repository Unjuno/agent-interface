# Native GUI unknown/yield gate

The clutter/occlusion native dataset was provenance-verified before training. A 354-parameter CNN trained on 80 frames and evaluated on 40 held-out frames. Gate: reject <0.25, yield 0.25..<0.75, accept >=0.75 positive softmax.

Held-out counts: negative accept 0/yield 0/reject 21; positive accept 18/yield 1/reject 0; accepted false positives 0.

This is a bounded controlled-GUI result, not calibration for DOOM or arbitrary applications. Provenance and yield remain required.
