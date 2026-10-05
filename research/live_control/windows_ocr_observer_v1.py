"""Persistent, local Windows OCR adapter for exact visible-token checks."""

import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import tempfile
import threading
import time


HERE = Path(__file__).resolve().parent
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")
TOKEN_BOUNDARY = r"(?<![A-Za-z0-9_-]){}(?![A-Za-z0-9_-])"


def exact_token_present(text, token):
    """Return true only when a complete token occurs in the OCR text."""
    if type(text) is not str:
        raise ValueError("OCR text must be a string")
    if type(token) is not str or not TOKEN_PATTERN.fullmatch(token):
        raise ValueError("expected token must be a bounded ASCII identifier")
    return re.search(TOKEN_BOUNDARY.format(re.escape(token)), text) is not None


def exact_token_state(text, token):
    """Return a tri-state value predicate; empty OCR output stays unknown."""
    if type(text) is not str:
        raise ValueError("OCR text must be a string")
    present = exact_token_present(text, token)
    if not text.strip():
        return "unknown"
    return present


class WindowsOcrObserver:
    """Own one PowerShell/WinRT worker and reuse its OCR engine across frames."""

    def __init__(self, *, language=None, timeout_seconds=8):
        if os.name != "nt":
            raise OSError("Windows OCR is only available on Windows")
        if (type(timeout_seconds) not in (int, float) or
                timeout_seconds <= 0):
            raise ValueError("positive timeout_seconds required")
        if language is not None and (type(language) is not str or not language):
            raise ValueError("language must be a nonempty language tag or None")
        powershell = shutil.which("powershell.exe")
        if powershell is None:
            raise FileNotFoundError("Windows PowerShell 5.1 is unavailable")
        command = [powershell, "-NoLogo", "-NoProfile", "-NonInteractive",
                   "-File", str(HERE / "windows_ocr_worker_v1.ps1")]
        if language is not None:
            command.extend(["-RequestedLanguage", language])
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        self._process = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
            errors="strict", bufsize=1, startupinfo=startupinfo)
        self._timeout = float(timeout_seconds)
        self._responses = queue.Queue()
        self._lock = threading.Lock()
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()
        try:
            ready = self._next_response()
        except Exception:
            self.close()
            raise
        if (ready.get("status") != "ready" or
                type(ready.get("language")) is not str):
            self.close()
            raise RuntimeError("Windows OCR worker did not become ready")
        self.language = ready["language"]

    def _read_stdout(self):
        try:
            for line in self._process.stdout:
                self._responses.put(line)
        finally:
            self._responses.put(None)

    def _next_response(self):
        try:
            line = self._responses.get(timeout=self._timeout)
        except queue.Empty as error:
            raise TimeoutError("Windows OCR worker response timed out") from error
        if line is None:
            raise RuntimeError("Windows OCR worker exited")
        try:
            response = json.loads(line)
        except json.JSONDecodeError as error:
            raise RuntimeError("Windows OCR worker returned invalid JSON") from error
        if type(response) is not dict:
            raise RuntimeError("Windows OCR worker response must be an object")
        if response.get("status") == "error":
            raise RuntimeError("Windows OCR failed: " + str(response.get("error")))
        return response

    def recognize(self, image_path, *, region=None, scale=1):
        path = Path(image_path).resolve(strict=True)
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
            raise ValueError("OCR image must be PNG, JPEG, or BMP")
        if path.stat().st_size > 10 * 1024 * 1024:
            raise ValueError("OCR image exceeds 10 MiB")
        if (type(scale) not in (int, float) or not math.isfinite(scale) or
                not 1 <= scale <= 8):
            raise ValueError("scale must be between 1 and 8")
        if region is not None and (
                type(region) not in (tuple, list) or len(region) != 4 or
                any(type(value) is not int for value in region)):
            raise ValueError("region must be integer x, y, width, height")

        started_ns = time.perf_counter_ns()
        processed_path = None
        try:
            if region is not None or scale != 1:
                try:
                    from PIL import Image
                except ImportError as error:
                    raise RuntimeError("Pillow is required for crop/upscale OCR") from error
                with Image.open(path) as opened:
                    source = opened.convert("RGB")
                try:
                    if region is not None:
                        x, y, width, height = region
                        if (x < 0 or y < 0 or width <= 0 or height <= 0 or
                                x + width > source.width or y + height > source.height):
                            raise ValueError("OCR region must fit inside the image")
                        cropped = source.crop((x, y, x + width, y + height))
                        source.close()
                        source = cropped
                    out_width = round(source.width * scale)
                    out_height = round(source.height * scale)
                    if (out_width < 1 or out_height < 1 or out_width > 4096 or
                            out_height > 4096 or out_width * out_height > 16_000_000):
                        raise ValueError("processed OCR image exceeds size limits")
                    if scale != 1:
                        resized = source.resize((out_width, out_height),
                                                Image.Resampling.LANCZOS)
                        source.close()
                        source = resized
                    handle = tempfile.NamedTemporaryFile(
                        prefix="interface-ocr-", suffix=".png", delete=False)
                    processed_path = Path(handle.name)
                    handle.close()
                    source.save(processed_path, format="PNG")
                finally:
                    source.close()

            request_path = path if processed_path is None else processed_path
            request = json.dumps({"operation": "recognize",
                                  "path": str(request_path)},
                                 ensure_ascii=False)
            if len(request) > 8192:
                raise ValueError("OCR request exceeds 8192 characters")
            with self._lock:
                if self._process.poll() is not None:
                    raise RuntimeError("Windows OCR worker exited")
                try:
                    self._process.stdin.write(request + "\n")
                    self._process.stdin.flush()
                except (BrokenPipeError, OSError) as error:
                    raise RuntimeError("Windows OCR worker input failed") from error
                response = self._next_response()
        finally:
            if processed_path is not None:
                processed_path.unlink(missing_ok=True)
        elapsed_ns = time.perf_counter_ns() - started_ns
        if (response.get("status") != "ok" or
                response.get("language") != self.language or
                type(response.get("text")) is not str):
            raise RuntimeError("Windows OCR worker returned an invalid result")
        return {"status": "ok", "language": self.language,
                "text": response["text"], "elapsed_ns": elapsed_ns}

    def close(self):
        process = getattr(self, "_process", None)
        if process is None:
            return
        if process.poll() is None:
            try:
                process.stdin.close()
                process.wait(timeout=2)
            except (OSError, subprocess.TimeoutExpired):
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        reader = getattr(self, "_reader", None)
        if reader is not None:
            reader.join(timeout=2)
        for stream in (process.stdin, process.stdout):
            if stream is not None and not stream.closed:
                stream.close()

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        self.close()
