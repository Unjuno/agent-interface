import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--git-tree", help="also verify the package blobs in this Git tree/ref")
args = parser.parse_args()
raw = json.loads((root / "raw-result.txt").read_text(encoding="utf-8"))
assert raw["child_returncode"] == -2, raw
assert raw["persisted_summary"] == {"verdict": "PASS_SCOPED_PIPE_NOTIFICATION"}, raw
assert raw["child_stderr_has_keyboard_interrupt"] is True, raw

entries = {}
for line in (root / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines():
    match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_./-]+)", line)
    assert match, f"malformed checksum line: {line!r}"
    expected, relative = match.groups()
    path = Path(relative)
    assert not path.is_absolute() and ".." not in path.parts, relative
    assert relative not in entries, relative
    entries[relative] = expected
    target = (root / path).resolve()
    assert target.is_relative_to(root.resolve()), relative
    data = target.read_bytes()
    assert hashlib.sha256(data).hexdigest() == expected, relative
    assert not any(byte < 32 and byte not in (9, 10, 13) for byte in data), relative
actual_files = {
    path.relative_to(root).as_posix()
    for path in root.rglob("*")
    if path.is_file() and path.name not in {"SHA256SUMS.txt", ".gitattributes"}
}
assert set(entries) == actual_files, {"missing": sorted(actual_files - set(entries)),
                                       "extra": sorted(set(entries) - actual_files)}
if args.git_tree:
    top = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()).resolve()
    prefix = root.resolve().relative_to(top).as_posix().rstrip("/") + "/"
    tracked = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", args.git_tree, "--", prefix], text=True).splitlines()
    tree_files = {name[len(prefix):] for name in tracked
                  if name.startswith(prefix) and name[len(prefix):] not in {"SHA256SUMS.txt", ".gitattributes"}}
    assert tree_files == set(entries), {"tree_missing": sorted(set(entries) - tree_files),
                                        "tree_extra": sorted(tree_files - set(entries))}
    for relative, expected in entries.items():
        data = subprocess.check_output(["git", "show", f"{args.git_tree}:{prefix}{relative}"])
        assert hashlib.sha256(data).hexdigest() == expected, f"git blob mismatch: {relative}"
        assert not any(byte < 32 and byte not in (9, 10, 13) for byte in data), relative
print("PASS_SYNTHETIC_SIGNAL_ORDER_AND_PACKAGE_BYTES" +
      (f"_AND_GIT_TREE({args.git_tree})" if args.git_tree else "") +
      ": child SIGINT (-2), persisted PASS, complete hashes, no text control bytes")
