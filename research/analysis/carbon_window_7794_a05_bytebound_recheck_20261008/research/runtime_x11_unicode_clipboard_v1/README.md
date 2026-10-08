# X11 Unicode clipboard lowering v1

Research-only candidate for non-ASCII text on X11. It deliberately treats UTF-8 clipboard paste as a side-effecting lowering mechanism and measures clipboard ownership/restoration separately from durable application semantics. It does not modify the shared runtime or the portable contract.
