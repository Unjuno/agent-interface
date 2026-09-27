#!/usr/bin/env python3
"""Fetch/verify pinned public assets and optionally extract a private Linux prefix."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--extract", action="store_true")
    a = ap.parse_args()
    root = a.root.resolve()
    assets = json.loads((HERE / "assets.json").read_text())["assets"]
    for item in assets:
        path = (root / item["path"]).resolve()
        assert path.is_relative_to(root)
        if not path.exists() and a.download:
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_suffix(path.suffix + ".download")
            with urllib.request.urlopen(item["url"], timeout=120) as response, temp.open("wb") as f:
                while chunk := response.read(1024 * 1024):
                    f.write(chunk)
            assert temp.stat().st_size == item["bytes"]
            assert hashlib.sha256(temp.read_bytes()).hexdigest() == item["sha256"]
            temp.replace(path)
        assert path.stat().st_size == item["bytes"], path
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], path
        if a.extract and path.suffix == ".deb":
            prefix = root / ("luanti-root" if path.name == "luanti-5.17.0.deb" else "root")
            subprocess.run(["dpkg-deb", "-x", str(path), str(prefix)], check=True)
    if a.extract:
        share = root / "root/usr/share/minetest"
        if not share.exists():
            share.symlink_to("games/minetest")
    print(json.dumps({"verified_assets": len(assets), "bytes": sum(x["bytes"] for x in assets),
                      "extracted": a.extract}))


if __name__ == "__main__":
    main()
