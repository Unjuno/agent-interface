"""Package, without rewriting, each formal seed's raw builder/loader evidence."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
RUN = ROOT / "outputs" / "formal01"
DEST = RUN / "bundles"
SEEDS = [2026092700, 2026092800, 2026092900, 2026093000, 2026093100,
         2026093200, 2026093300, 2026093400, 2026093500, 2026093600]
FILES = ["builder/skill.json", "builder/expected.json", "load1/loader.json",
         "load2/loader.json", "builder.log", "load1.log", "load2.log"]


def main():
    DEST.mkdir(exist_ok=True)
    manifest = []
    for seed in SEEDS:
        source = RUN / f"seed-{seed}"
        target = DEST / f"seed-{seed}.zip"
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for relative in FILES:
                data = (source / relative).read_bytes()
                archive.writestr(relative, data)
        raw = target.read_bytes()
        manifest.append({"seed": seed, "path": target.name, "bytes": len(raw),
                         "sha256": hashlib.sha256(raw).hexdigest(), "members": FILES})
    (DEST / "EVIDENCE_MANIFEST.json").write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"bundles": manifest, "total_bytes": sum(x["bytes"] for x in manifest)},
                     sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()

