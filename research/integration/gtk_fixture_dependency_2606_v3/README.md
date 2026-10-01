# GTK/Xlib dependency successor (#2844)

This additive image preserves the #2748 GTK image and adds Debian
python3-xlib, the dependency missing in the #2836 bounded allocation. It is
only a dependency/import preflight; it does not send GUI input, run the matrix,
or claim formal #2606 acceptance.

The image uses the same immutable Python base digest and exposes Debian
site-packages. A later allocation must retain this image identity and remain
scoped as unscored until capture-time receipts are repaired.
