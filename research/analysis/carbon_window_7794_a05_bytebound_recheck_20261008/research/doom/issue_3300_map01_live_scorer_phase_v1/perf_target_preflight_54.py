"""Read-only Linux perf permission and ViZDoom engine symbol preflight."""
import ctypes
import json
import os
import platform
import struct
from pathlib import Path

import vizdoom as vd

FIX = Path("/fixture/fixture")
manifest = json.loads((FIX / "fixture.json").read_text())


def self_perf_event_open():
    # Linux AArch64 uses the asm-generic syscall number 241.
    attr = bytearray(128)
    # PERF_TYPE_SOFTWARE=1, PERF_COUNT_SW_CPU_CLOCK=0, disabled=1.
    struct.pack_into("<IIQQQQQ", attr, 0, 1, 128, 0, 0, 0, 0, 1)
    buf = ctypes.create_string_buffer(bytes(attr), len(attr))
    libc = ctypes.CDLL(None, use_errno=True)
    fd = libc.syscall(241, ctypes.byref(buf), 0, -1, -1, 0)
    if fd < 0:
        err = ctypes.get_errno()
        return {"result": "STOP", "errno": err, "error": os.strerror(err)}
    os.close(fd)
    return {"result": "PASS", "fd_opened": True}


def elf_clock_symbols(path: Path):
    data = path.read_bytes()
    if data[:4] != b"\x7fELF" or data[4:6] != b"\x02\x01":
        return {"elf64_little_endian": False, "symbols": []}
    shoff = struct.unpack_from("<Q", data, 40)[0]
    shentsize, shnum, shstrndx = struct.unpack_from("<HHH", data, 58)
    sections = [
        struct.unpack_from("<IIQQQQIIQQ", data, shoff + i * shentsize)
        for i in range(shnum)
    ]
    shstr = sections[shstrndx]
    section_names = data[shstr[4]:shstr[4] + shstr[5]]
    found = []
    for section in sections:
        secname = section_names[section[0]:].split(b"\0", 1)[0].decode(errors="replace")
        if secname not in (".symtab", ".dynsym") or not section[9]:
            continue
        string_section = sections[section[6]]
        strings = data[string_section[4]:string_section[4] + string_section[5]]
        for offset in range(section[4], section[4] + section[5], section[9]):
            name_offset, info, other, shndx, value, size = struct.unpack_from(
                "<IBBHQQ", data, offset
            )
            name = strings[name_offset:].split(b"\0", 1)[0].decode(errors="replace")
            if "viz_tic" in name.lower() or "map_tic" in name.lower():
                found.append({"section": secname, "name": name, "value": hex(value), "size": size})
    return {"elf64_little_endian": True, "symbols": found}


def seccomp_mode():
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("Seccomp:"):
            return int(line.split()[1])
    return None


def main():
    result = {
        "schema": "map01-perf-target-preflight-v1",
        "formal_allocation": False,
        "kernel": platform.release(),
        "machine": platform.machine(),
        "seccomp": seccomp_mode(),
        "perf_event_paranoid": Path("/proc/sys/kernel/perf_event_paranoid").read_text().strip(),
        "self_perf_event_open": self_perf_event_open(),
        "vizdoom": vd.__version__,
        "fixture_sha256": __import__("hashlib").sha256((FIX / "fixture.json").read_bytes()).hexdigest(),
    }
    wad = Path(vd.__file__).parent / "freedoom2.wad"
    if __import__("hashlib").sha256(wad.read_bytes()).hexdigest() != manifest["iwad_sha256"]:
        raise SystemExit("STOP_WAD_HASH")
    game = vd.DoomGame()
    game.set_doom_game_path(str(wad))
    game.set_doom_scenario_path("")
    game.set_doom_map(manifest["map"])
    game.set_doom_skill(manifest["skill"])
    game.set_seed(manifest["seed"])
    game.set_mode(vd.Mode.ASYNC_SPECTATOR)
    game.set_ticrate(35)
    game.set_window_visible(True)
    game.set_sound_enabled(False)
    game.init()
    game.load(str(FIX / manifest["save_file"]))
    try:
        candidates = []
        for proc in Path("/proc").iterdir():
            if not proc.name.isdigit():
                continue
            try:
                exe = (proc / "exe").resolve()
                if exe.name == "vizdoom":
                    candidates.append({"path": str(exe), **elf_clock_symbols(proc / "exe")})
            except OSError:
                continue
        result["engine_candidates"] = candidates
    finally:
        game.close()
    result["disposition"] = (
        "HOLD_TARGET_ADDRESS_UNRESOLVED"
        if not any(row.get("symbols") for row in result["engine_candidates"])
        else "TARGET_SYMBOL_CANDIDATE_FOUND_NOT_VALIDATED"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
