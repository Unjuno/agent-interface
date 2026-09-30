"""One real Calc unsaved-edit construction case; no save/store call is made."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import socket
import subprocess
import time

import uno
from openpyxl import Workbook, load_workbook


OUT = pathlib.Path("/out")
RUN = OUT / "calc-effect-contract-34-pilot-20260927-01"
DISPLAY = ":99"
PORT = 2002


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def connect_calc(deadline: float):
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local
    )
    while time.monotonic() < deadline:
        try:
            ctx = resolver.resolve(
                f"uno:socket,host=127.0.0.1,port={PORT};urp;StarOffice.ComponentContext"
            )
            desktop = ctx.ServiceManager.createInstanceWithContext(
                "com.sun.star.frame.Desktop", ctx
            )
            doc = desktop.getCurrentComponent()
            if doc is not None and doc.supportsService("com.sun.star.sheet.SpreadsheetDocument"):
                return desktop, doc
        except Exception:
            time.sleep(0.2)
    raise TimeoutError("Calc UNO document did not become available")


def main() -> int:
    if RUN.exists():
        raise FileExistsError(f"refusing to overwrite prior run: {RUN}")
    RUN.mkdir(parents=True)
    source = RUN / "baseline.xlsx"
    wb = Workbook()
    ws = wb.active
    ws["A1"] = 0
    ws["B1"] = "baseline"
    wb.save(source)
    wb.close()
    before_sha = sha256(source)

    os.environ["DISPLAY"] = DISPLAY
    xvfb = subprocess.Popen(
        ["Xvfb", DISPLAY, "-screen", "0", "1280x800x24", "-nolisten", "tcp"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    time.sleep(0.5)
    profile = pathlib.Path("/tmp/calc-effect-contract-profile")
    profile_uri = profile.as_uri()
    soffice = subprocess.Popen(
        [
            "soffice",
            "--norestore",
            "--nofirststartwizard",
            "--nodefault",
            "--nologo",
            f"-env:UserInstallation={profile_uri}",
            f"--accept=socket,host=127.0.0.1,port={PORT};urp;StarOffice.ServiceManager",
            str(source),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env=os.environ.copy(),
    )
    try:
        desktop, doc = connect_calc(time.monotonic() + 30)
        sheet = doc.getSheets().getByIndex(0)
        cell = sheet.getCellRangeByName("A1")
        value_before = cell.getValue()
        cell.setValue(7)
        live_value = cell.getValue()
        modified = bool(doc.isModified())
        visible_windows = subprocess.run(
            ["xdotool", "search", "--onlyvisible", "--class", "soffice"],
            text=True,
            capture_output=True,
            timeout=5,
        )
        window_ids = [x for x in visible_windows.stdout.splitlines() if x.strip()]
        # Independent disk-side read while Calc still holds the unsaved edit.
        on_disk = load_workbook(source, read_only=True, data_only=True)
        persisted_value = on_disk.active["A1"].value
        on_disk.close()
        after_sha = sha256(source)
        raw = {
            "schema": "calc-effect-contract-unsaved-boundary-v1",
            "allocation": "calc-effect-contract-34-pilot-20260927-01",
            "container_display": DISPLAY,
            "soffice_pid": soffice.pid,
            "xvfb_pid": xvfb.pid,
            "image": "issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393",
            "application": "LibreOffice Calc",
            "application_version": subprocess.run(
                ["soffice", "--version"], text=True, capture_output=True, timeout=10
            ).stdout.strip(),
            "source_file": "baseline.xlsx",
            "source_sha256_before": before_sha,
            "source_sha256_after": after_sha,
            "cell_before_edit": value_before,
            "cell_after_edit_live": live_value,
            "document_modified_unsaved": modified,
            "visible_calc_window_ids": window_ids,
            "program_completed": True,
            "save_store_calls": 0,
            "persisted_cell_after_independent_reopen": persisted_value,
            "raw_classifications": {
                "program_terminal_shortcut": "VERIFIED",
                "live_required_effect_shortcut": "VERIFIED",
                "saved_effect_contract": "CONTRADICTED"
                if persisted_value != 7
                else "VERIFIED",
            },
            "scope": "single construction case; no model, physical input, or formal allocation",
        }
        (RUN / "raw.json").write_text(
            json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(raw, sort_keys=True))
        return 0
    finally:
        # The container is disposable; terminate the unsaved application without saving.
        for process in (soffice, xvfb):
            if process.poll() is None:
                process.kill()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass


if __name__ == "__main__":
    raise SystemExit(main())
