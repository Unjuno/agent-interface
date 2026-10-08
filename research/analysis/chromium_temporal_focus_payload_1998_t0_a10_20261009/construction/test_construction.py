#!/usr/bin/env python3
"""Synthetic codec/mount test; never reads the frozen Chromium inputs."""
import hashlib
import copy
import importlib.util
import json
import sys
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
IMAGE = "node@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80"
SIG = b"\x89PNG\r\n\x1a\n"


def crc_chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)


def paeth(a, b, c):
    p = a + b - c
    return min(((abs(p-a), a), (abs(p-b), b), (abs(p-c), c)), key=lambda pair: pair[0])[1]


def make_png(width, height, pixels):
    stride, bpp = width * 3, 3
    scan = bytearray()
    for y in range(height):
        filt = y % 5
        scan.append(filt)
        row = pixels[y*stride:(y+1)*stride]
        prev = pixels[(y-1)*stride:y*stride] if y else bytes(stride)
        for x, value in enumerate(row):
            left = row[x-bpp] if x >= bpp else 0
            up = prev[x]
            upper_left = prev[x-bpp] if x >= bpp else 0
            if filt == 0: predictor = 0
            elif filt == 1: predictor = left
            elif filt == 2: predictor = up
            elif filt == 3: predictor = (left + up) // 2
            else: predictor = paeth(left, up, upper_left)
            scan.append((value - predictor) & 255)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return SIG + crc_chunk(b"IHDR", ihdr) + crc_chunk(b"IDAT", zlib.compress(bytes(scan), 6)) + crc_chunk(b"IEND", b"")


def decode_rgb(data):
    pos, width, height, pieces = 8, None, None, []
    while pos < len(data):
        size = struct.unpack_from(">I", data, pos)[0]; pos += 4
        kind = data[pos:pos+4]; pos += 4
        chunk = data[pos:pos+size]; pos += size
        crc = struct.unpack_from(">I", data, pos)[0]; pos += 4
        assert zlib.crc32(kind + chunk) & 0xffffffff == crc
        if kind == b"IHDR": width, height, depth, color, *_ = struct.unpack(">IIBBBBB", chunk); assert (depth, color) == (8, 2)
        elif kind == b"IDAT": pieces.append(chunk)
        elif kind == b"IEND": break
    stride, bpp = width * 3, 3
    raw = zlib.decompress(b"".join(pieces)); out = bytearray(height * stride); cur = 0
    for y in range(height):
        filt = raw[cur]; cur += 1; row = y * stride
        for x in range(stride):
            v = raw[cur]; cur += 1
            left = out[row+x-bpp] if x >= bpp else 0
            up = out[row-stride+x] if y else 0
            ul = out[row-stride+x-bpp] if y and x >= bpp else 0
            pred = (0 if filt == 0 else left if filt == 1 else up if filt == 2 else (left+up)//2 if filt == 3 else paeth(left,up,ul))
            out[row+x] = (v+pred)&255
    return width,height,bytes(out)


def main():
    pixels = bytes((i * 37 + 11) & 255 for i in range(5 * 4 * 3))
    source = make_png(5, 4, pixels)
    with tempfile.TemporaryDirectory(prefix="a10-construction-") as tmp:
        root = Path(tmp)
        src = root / "src"; src.mkdir(); (src / "src").mkdir()
        inputs = root / "inputs"; inputs.mkdir()
        outputs = root / "results"; outputs.mkdir()
        (src / "src" / "candidate.js").write_bytes((PKG / "src" / "candidate.js").read_bytes())
        frame_name = "fixture.png"; (inputs / frame_name).write_bytes(source)
        manifest = {
            "allocation":"CONSTRUCTION_ONLY",
            "roi":{"x":1,"y":1,"width":3,"height":2},
            "frames":[{"sequence":1,"frame_id":"fixture-frame","file":frame_name,
              "png_sha256":hashlib.sha256(source).hexdigest(),"source_pixel_sha256":hashlib.sha256(pixels).hexdigest(),
              "width":5,"height":4,"action_id":"fixture","reason":"construction"}],
        }
        (src / "manifest.json").write_text(json.dumps(manifest))
        command = ["docker","run","--rm","--pull=never","--network","none","--read-only",
          "--cap-drop=ALL","--security-opt=no-new-privileges","--pids-limit=32","--cpus=1","--memory=256m",
          "--user","1000:1000","--tmpfs","/tmp:rw,nosuid,nodev,noexec,size=16m",
          "--mount",f"type=bind,src={src},dst=/src,readonly",
          "--mount",f"type=bind,src={inputs},dst=/inputs,readonly",
          "--mount",f"type=bind,src={outputs},dst=/results",
          IMAGE,"node","/src/src/candidate.js"]
        run = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if run.returncode != 0:
            raise SystemExit(f"construction container failed: exit={run.returncode} stderr={run.stderr[-1000:]}")
        result = json.loads((outputs / "candidate.json").read_text())
        crop = (outputs / "artifacts" / "1.png").read_bytes()
        cw,ch,actual = decode_rgb(crop)
        expected = b"".join(pixels[((1+y)*5+1)*3:((1+y)*5+4)*3] for y in range(2))
        assert (cw,ch,actual) == (3,2,expected)
        assert result["rows"][0]["crop_pixel_sha256"] == hashlib.sha256(expected).hexdigest()
        assert result["summary"]["distinct_roi_states"] == 1
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("a10_auditor", PKG / "auditor.py")
        auditor = importlib.util.module_from_spec(spec); spec.loader.exec_module(auditor)
        assert auditor.validate(result, manifest, root, inputs) == []
        mutations = [
            lambda value: value["rows"][0].__setitem__("sequence", 99),
            lambda value: value["rows"][0].__setitem__("crop_file", "../escape.png"),
            lambda value: value["rows"][0].__setitem__("crop_png_sha256", "0" * 64),
            lambda value: value["rows"][0].__setitem__("focused_payload_bytes", 0),
            lambda value: value["summary"].__setitem__("saved_bytes", -1),
            lambda value: value["rows"][0].__setitem__("source_pixel_sha256", "f" * 64),
        ]
        rejected = 0
        for mutate in mutations:
            changed = copy.deepcopy(result); mutate(changed)
            rejected += bool(auditor.validate(changed, manifest, root, inputs))
        assert rejected == 6
        import ast
        ast.parse((PKG / "auditor.py").read_text())
        print(json.dumps({"status":"PASS_CONSTRUCTION_ONLY","png_filters_tested":[0,1,2,3,4],"roi_pixels_exact":True,
          "metadata_included_payload_saving":result["summary"]["saved_bytes"],"candidate_exit":run.returncode,
          "container_image":IMAGE,"container_stdout":run.stdout.strip()},sort_keys=True))


if __name__ == "__main__":
    main()
