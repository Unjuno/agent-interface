"""One-session excluded hardware-breakpoint probe for ViZDoom VIZ_Tic."""
import ctypes
import hashlib
import json
import mmap
import os
import struct
import sys
import time
from pathlib import Path

import vizdoom as vd
sys.path.insert(0, "/current")
from session_map01_v13 import _coherent_progress_sample

WAD = Path(vd.__file__).parent / "freedoom2.wad"
FIX = Path("/fixture/fixture")
MANIFEST = json.loads((FIX / "fixture.json").read_text())
BASELINE = Path("/compare/vizdoom-baseline")
VIZ_TIC_LINK_ADDRESS = 0x3EEE80


def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def elf_layout(path):
    data = path.read_bytes()
    if data[:6] != b"\x7fELF\x02\x01":
        raise ValueError("expected ELF64 little-endian")
    elf_type = struct.unpack_from("<H", data, 16)[0]
    phoff = struct.unpack_from("<Q", data, 32)[0]
    phentsize, phnum = struct.unpack_from("<HH", data, 54)
    loads = []
    for i in range(phnum):
        p_type, flags, p_offset, p_vaddr, p_paddr, filesz, memsz, align = struct.unpack_from(
            "<IIQQQQQQ", data, phoff + i * phentsize
        )
        if p_type == 1:
            loads.append({"offset": p_offset, "vaddr": p_vaddr, "flags": flags, "align": align})
    return data, elf_type, loads


def process_for_engine(expected_sha):
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit() or int(proc.name) <= 1:
            continue
        try:
            path = proc / "exe"
            resolved = path.resolve()
            if resolved.name != "vizdoom" or sha_file(path) != expected_sha:
                continue
            return int(proc.name), path, resolved, (proc / "maps").read_text()
        except OSError:
            continue
    raise RuntimeError("matching engine child not found")


def load_bias(maps_text, resolved_path, loads, page_size):
    zero_load = next(x for x in loads if x["offset"] == 0)
    map_path = str(resolved_path)
    for line in maps_text.splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) < 6 or fields[2] != "00000000" or fields[5].removesuffix(" (deleted)") != map_path:
            continue
        start = int(fields[0].split("-", 1)[0], 16)
        return start - (zero_load["vaddr"] // page_size * page_size), line
    raise RuntimeError("zero-offset engine mapping not found")


def perf_open(pid, runtime_address):
    # PERF_TYPE_BREAKPOINT, sample each HW_BREAKPOINT_X hit and use CLOCK_MONOTONIC.
    attr = bytearray(128)
    struct.pack_into("<IIQQQQQ", attr, 0, 5, 128, 0, 1, 7, 0, 1 | (1 << 25))
    struct.pack_into("<I", attr, 48, 1)  # wakeup_events
    struct.pack_into("<IQQ", attr, 52, 4, runtime_address, 4)  # execute breakpoint, 4-byte instruction
    struct.pack_into("<i", attr, 92, 1)  # CLOCK_MONOTONIC
    buffer = ctypes.create_string_buffer(bytes(attr), len(attr))
    libc = ctypes.CDLL(None, use_errno=True)
    fd = libc.syscall(241, ctypes.byref(buffer), pid, -1, -1, 0)
    if fd < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), "perf_event_open")
    return fd, libc


def ring_records(ring, page_size):
    data_head = struct.unpack_from("<Q", ring, 1024)[0]
    data_tail = struct.unpack_from("<Q", ring, 1032)[0]
    data_offset = struct.unpack_from("<Q", ring, 1040)[0] or page_size
    data_size = struct.unpack_from("<Q", ring, 1048)[0] or (len(ring) - data_offset)
    records = []
    cursor = data_tail
    while cursor < data_head:
        offset = cursor % data_size
        header_bytes = ring[data_offset + offset:data_offset + offset + 8]
        if len(header_bytes) < 8:
            break
        record_type, misc, size = struct.unpack("<IHH", header_bytes)
        if size < 8 or size > data_size:
            break
        first = min(size, data_size - offset)
        blob = ring[data_offset + offset:data_offset + offset + first]
        if first < size:
            blob += ring[data_offset:data_offset + size - first]
        if record_type == 9 and size >= 32:
            ip, pid, tid, stamp = struct.unpack_from("<QIIQ", blob, 8)
            records.append({"type": "sample", "ip": hex(ip), "pid": pid, "tid": tid, "time_ns": stamp})
        elif record_type == 2 and size >= 24:
            event_id, lost = struct.unpack_from("<QQ", blob, 8)
            records.append({"type": "lost", "id": event_id, "lost": lost})
        else:
            records.append({"type": "other", "record_type": record_type, "size": size})
        cursor += size
    struct.pack_into("<Q", ring, 1032, data_head)
    return records, data_head, data_tail, data_offset, data_size


def main():
    if sha_file(WAD) != MANIFEST["iwad_sha256"] or vd.__version__ != "1.3.0":
        raise SystemExit("STOP_RUNTIME_IDENTITY")
    if sha_file(FIX / MANIFEST["save_file"]) != MANIFEST["save_sha256"]:
        raise SystemExit("STOP_FIXTURE_IDENTITY")
    result = {
        "schema": "map01-viz-tic-hwbp-construction-v1",
        "formal_allocation": False,
        "vizdoom": vd.__version__,
        "mode": "ASYNC_SPECTATOR",
        "requested_ticrate": 35,
        "fixture_sha256": sha_file(FIX / "fixture.json"),
        "save_sha256": sha_file(FIX / MANIFEST["save_file"]),
        "wad_sha256": sha_file(WAD),
        "baseline_binary_sha256": sha_file(BASELINE),
        "viz_tic_link_address": hex(VIZ_TIC_LINK_ADDRESS),
    }
    game = vd.DoomGame()
    game.set_doom_game_path(str(WAD))
    game.set_doom_scenario_path("")
    game.set_doom_map(MANIFEST["map"])
    game.set_doom_skill(MANIFEST["skill"])
    game.set_seed(MANIFEST["seed"])
    game.set_mode(vd.Mode.ASYNC_SPECTATOR)
    game.set_ticrate(35)
    game.set_window_visible(True)
    game.set_sound_enabled(False)
    game.set_available_game_variables([vd.GameVariable.KILLCOUNT, vd.GameVariable.DEATHCOUNT])
    game.init()
    game.load(str(FIX / MANIFEST["save_file"]))
    game.advance_action(1, True)
    result["api_tic_before_window"] = int(game.get_episode_time())
    engine_sha = result["baseline_binary_sha256"]
    pid, proc_exe, resolved, maps = process_for_engine(engine_sha)
    binary, elf_type, loads = elf_layout(BASELINE)
    page_size = os.sysconf("SC_PAGE_SIZE")
    bias, mapping = load_bias(maps, resolved, loads, page_size)
    address = bias + VIZ_TIC_LINK_ADDRESS
    exec_map = None
    for line in maps.splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) < 6 or fields[5].removesuffix(" (deleted)") != str(resolved):
            continue
        start, end = (int(value, 16) for value in fields[0].split("-", 1))
        if start <= address < end and "x" in fields[1]:
            exec_map = line
            break
    if exec_map is None:
        raise RuntimeError("target mapping is not executable")
    result.update({
        "engine_pid": pid,
        "engine_executable": str(resolved),
        "engine_executable_sha256": sha_file(proc_exe),
        "elf_type": elf_type,
        "load_bias": hex(bias),
        "runtime_viz_tic_address": hex(address),
        "zero_offset_mapping": mapping,
        "executable_mapping": exec_map,
        "perf_event_open": "pending",
    })
    fd = ring = None
    try:
        fd, libc = perf_open(pid, address)
        page_size = os.sysconf("SC_PAGE_SIZE")
        ring = mmap.mmap(fd, page_size * 9, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ | mmap.PROT_WRITE)
        libc.ioctl(fd, 0x2403, 0)  # RESET
        libc.ioctl(fd, 0x2400, 0)  # ENABLE
        start_perf = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        start_python = time.perf_counter_ns()
        time.sleep(0.25)
        scorer_start = time.perf_counter_ns()
        sample = _coherent_progress_sample(game, vd.GameVariable, 600)
        scorer_end = time.perf_counter_ns()
        time.sleep(0.4)
        end_python = time.perf_counter_ns()
        end_perf = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        libc.ioctl(fd, 0x2401, 0)  # DISABLE
        event_count = ctypes.c_longlong()
        bytes_read = libc.read(fd, ctypes.byref(event_count), ctypes.sizeof(event_count))
        records, head, tail, data_offset, data_size = ring_records(ring, page_size)
        result.update({
            "perf_event_open": "PASS",
            "perf_start_monotonic_ns": start_perf,
            "perf_end_monotonic_ns": end_perf,
            "python_start_perf_counter_ns": start_python,
            "python_end_perf_counter_ns": end_python,
            "scorer_start_ns": scorer_start,
            "scorer_end_ns": scorer_end,
            "scorer_return": sample.as_dict(),
            "api_tic_after_window": int(game.get_episode_time()),
            "event_read_bytes": bytes_read,
            "event_count": event_count.value,
            "ring_data_head": head,
            "ring_data_tail_before_read": tail,
            "ring_data_offset": data_offset,
            "ring_data_size": data_size,
            "records": records,
        })
    except OSError as exc:
        result.update({"perf_event_open": "STOP", "errno": exc.errno, "error": str(exc)})
    finally:
        if ring is not None:
            ring.close()
        if fd is not None:
            os.close(fd)
        game.close()
    result["disposition"] = (
        "PASS_BREAKPOINT_TIMESTAMP_CONSTRUCTION_ONLY"
        if result.get("event_count", 0) > 0 and any(r.get("type") == "sample" for r in result.get("records", []))
        else "HOLD_NO_BREAKPOINT_SAMPLES"
    )
    Path("/results/raw.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
