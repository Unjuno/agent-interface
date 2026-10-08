"""Compare symbol-bearing source build text with the pinned ViZDoom runtime."""
import hashlib
import json
import re
import struct
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def elf_text(path):
    data = path.read_bytes()
    if data[:6] != b"\x7fELF\x02\x01":
        raise ValueError(f"not ELF64 little-endian: {path}")
    section_offset = struct.unpack_from("<Q", data, 40)[0]
    entry_size, section_count, name_index = struct.unpack_from("<HHH", data, 58)
    sections = [
        struct.unpack_from("<IIQQQQIIQQ", data, section_offset + i * entry_size)
        for i in range(section_count)
    ]
    name_section = sections[name_index]
    names = data[name_section[4]:name_section[4] + name_section[5]]
    for section in sections:
        name = names[section[0]:].split(b"\0", 1)[0]
        if name == b".text":
            text = data[section[4]:section[4] + section[5]]
            return {"address": section[3], "size": section[5], "sha256": sha(text), "bytes": text}
    raise ValueError(f".text section not found: {path}")


def main():
    baseline_path = Path("/compare/vizdoom-baseline")
    stock_path = Path("/usr/local/lib/python3.11/site-packages/vizdoom/vizdoom")
    link_map = Path("/compare/vizdoom-baseline.map").read_text(errors="replace")
    match = re.search(r"^\s*0x([0-9a-fA-F]+)\s+VIZ_Tic\(\)\s*$", link_map, re.MULTILINE)
    if not match:
        raise SystemExit("VIZ_Tic_NOT_IN_LINK_MAP")
    function_address = int(match.group(1), 16)
    baseline, stock = elf_text(baseline_path), elf_text(stock_path)
    relative = function_address - baseline["address"]
    code = baseline["bytes"][relative:relative + 128]
    prefix_matches = {str(n): stock["bytes"].find(code[:n]) for n in (4, 8, 12, 16, 20, 24, 32, 48, 64, 128)}
    result = {
        "schema": "vizdoom-viz-tic-symbol-build-compare-v1",
        "formal_allocation": False,
        "source_commit": "c8e0a31182d98c6f40a65674283e736b851e8e59",
        "build_flags": "Release; CMAKE_CXX_FLAGS_RELEASE=-O3 -DNDEBUG -g; link map only",
        "baseline_binary_sha256": sha(baseline_path.read_bytes()),
        "stock_runtime_binary_sha256": sha(stock_path.read_bytes()),
        "baseline_text": {k: v for k, v in baseline.items() if k != "bytes"},
        "stock_runtime_text": {k: v for k, v in stock.items() if k != "bytes"},
        "viz_tic_link_address": hex(function_address),
        "viz_tic_relative_to_baseline_text": hex(relative),
        "viz_tic_first_128_bytes_sha256": sha(code),
        "viz_tic_prefix_matches_in_stock_text": prefix_matches,
        "exact_text_match": baseline["bytes"] == stock["bytes"],
        "disposition": "HOLD_BINARY_CODE_IDENTITY_NOT_ESTABLISHED",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
