# Xauthority cookie successor for #2699

This isolates X11 authentication construction after #2664. It launches the
three applications with the same generated MIT-MAGIC-COOKIE and records
validated xprop identities. It does not run the #2499 transition sequence.
