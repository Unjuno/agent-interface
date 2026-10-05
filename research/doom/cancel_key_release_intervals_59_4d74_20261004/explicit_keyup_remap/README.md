# Explicit key-up after a synthetic keymap change

## H — Hypothesis

After a logical key is admitted under one keysym-to-keycode mapping, changing that mapping before explicit key-up must not leave the originally admitted physical key down. Admission and explicit-up receipts should identify the same physical code.

## T — Test

The frozen one-case fake-Xlib test admits W as code 87, remaps W to 77, requests up for W, and checks the fake physical key state and owner receipts. The exact source/test hashes and command are in `FREEZE.json`.

## D — Decision

The pinned baseline should leave code 87 down and omit a matching explicit-up receipt. The candidate passes only when the fake key state is empty, admission and key-up both identify 87, and the release request is bounded by its XSync return.

## C — Competing interpretation

The remapped symbol may have different meaning, but a key-up paired with a currently held logical key must release the physical code admitted for that hold. Semantic interpretation still needs a keymap epoch.

## U — Limits

Synthetic Xlib only. No real X server remap delivery, physical key timing, GUI/game effect, model behavior, bounded recovery, or live threat response was tested.
