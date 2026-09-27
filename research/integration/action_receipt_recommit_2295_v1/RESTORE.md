# Read-only evidence restoration

This directory records a consumed STOP/HOLD allocation. Do **not** rerun `run.py` with the consumed allocation identity.

Reconstruct the retained raw evidence only:

```sh
cat parts/evidence.* | tr -d '\n' | base64 -d > /tmp/issue2295-evidence.tar.xz
echo "3cacb462933541d2de8f3fab08ac17f6b0a85763c925ffec6d74378ed7a9e178  /tmp/issue2295-evidence.tar.xz" | sha256sum -c -
mkdir /tmp/issue2295-evidence
tar -xJf /tmp/issue2295-evidence.tar.xz -C /tmp/issue2295-evidence
```

The archive contains 132 construction/formal evidence files. The formal first outcome has 49 complete rows of the frozen 54-row denominator and no terminal END record. `STOP.md` is authoritative for disposition.
