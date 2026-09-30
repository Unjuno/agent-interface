# Construction execution notes

These attempts occurred before the model inference and are kept separate from
the six frozen decision rows.

1. Inkscape 1.4 rejected `--new-window`; no modal was created.
2. Starting Inkscape without a file and sending Ctrl+Shift+S left only the main
   window; no modal capture was accepted.
3. Opening the local fixture SVG and sending Ctrl+Shift+S created a focused
   `Select file to save to` transient, but the first inline screenshot snippet
   contained literal `\n` characters and failed with Python `SyntaxError`.
4. A corrected capture succeeded. `evidence/windows-current.txt` records the main
   `fixture.svg - Inkscape` window and the focused `Select file to save to`
   transient. The returned PNG was visually checked before freeze validation.

The setup shortcut was confined to a disposable Docker Xvfb display and was
released before image capture. It did not write or alter the fixture SVG.
