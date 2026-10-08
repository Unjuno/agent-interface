"""One isolated Calc/Xvfb case for the local-amd64 #4667 successor."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import subprocess
import time
import zipfile
from xml.etree import ElementTree as ET

import uno

OUT = pathlib.Path("/out/case01")
DISPLAY = ":98"
PORT = 2004
IMAGE_ID = "sha256:854f930b93be86111d80cca5268ee6423777ec21588de55a5fb717332993379d"
ALLOCATION = "calc-doc-window-local-amd64-4667-v2-20260927-01"
STEM = "baseline-local-amd64-4667-v2"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_xlsx(path: pathlib.Path) -> None:
    files = {
        "[Content_Types].xml": b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>''',
        "_rels/.rels": b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>''',
        "xl/workbook.xml": b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets>
</workbook>''',
        "xl/_rels/workbook.xml.rels": b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>''',
        "xl/worksheets/sheet1.xml": b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="n"><v>0</v></c><c r="B1" t="inlineStr"><is><t>baseline</t></is></c></row>
</sheetData></worksheet>''',
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in files.items():
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, data)


def run(argv: list[str], timeout: float = 8) -> dict:
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        return {"argv": argv, "returncode": proc.returncode, "stdout": proc.stdout,
                "stderr": proc.stderr, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        return {"argv": argv, "returncode": None,
                "stdout": (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or ""),
                "stderr": (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or ""),
                "timed_out": True}


def main() -> int:
    for variable in ("HOME", "XDG_CACHE_HOME", "XDG_CONFIG_HOME"):
        value = os.environ.get(variable)
        if value:
            pathlib.Path(value).mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=False)
    workbook = OUT / f"{STEM}.xlsx"
    write_xlsx(workbook)
    before_hash = digest(workbook.read_bytes())
    xvfb_log = (OUT / "xvfb.stderr").open("wb")
    soffice_log = None
    xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1280x800x24", "-nolisten", "tcp"],
                            stdout=subprocess.DEVNULL, stderr=xvfb_log)
    soffice = None
    try:
        os.environ["DISPLAY"] = DISPLAY
        deadline = time.monotonic() + 10
        root_probe = None
        while time.monotonic() < deadline:
            root_probe = run(["xwininfo", "-root"], timeout=2)
            if root_probe["returncode"] == 0:
                break
            time.sleep(0.1)
        if not root_probe or root_probe["returncode"] != 0:
            raise RuntimeError("STOP_XVFB_NOT_READY")

        profile = pathlib.Path("/tmp/calc-doc-window-local-amd64-profile")
        soffice_log = (OUT / "soffice.stderr").open("wb")
        soffice = subprocess.Popen([
            "soffice", "--norestore", "--nofirststartwizard", "--nodefault", "--nologo",
            f"-env:UserInstallation={profile.as_uri()}",
            f"--accept=socket,host=127.0.0.1,port={PORT};urp;StarOffice.ServiceManager",
        ], stdout=subprocess.DEVNULL, stderr=soffice_log, env=os.environ.copy())

        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
        ctx = None
        for _ in range(150):
            try:
                ctx = resolver.resolve(f"uno:socket,host=127.0.0.1,port={PORT};urp;StarOffice.ComponentContext")
                break
            except Exception:
                if soffice.poll() is not None:
                    raise RuntimeError("STOP_SOFFICE_EXITED_DURING_STARTUP")
                time.sleep(0.2)
        if ctx is None:
            raise RuntimeError("STOP_UNO_CONNECT_TIMEOUT")
        desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
        props = (uno.createUnoStruct("com.sun.star.beans.PropertyValue"),)
        props[0].Name = "Hidden"
        props[0].Value = False
        doc = desktop.loadComponentFromURL(workbook.as_uri(), "_blank", 0, props)
        if doc is None or not doc.supportsService("com.sun.star.sheet.SpreadsheetDocument"):
            raise RuntimeError("STOP_CALC_DOCUMENT_NOT_OPEN")
        cell = doc.getSheets().getByIndex(0).getCellRangeByName("A1")
        before_value = cell.getValue()
        cell.setValue(7)
        after_value = cell.getValue()
        is_modified = bool(doc.isModified())
        time.sleep(0.5)
        tree = run(["xwininfo", "-root", "-tree"])
        text = tree["stdout"]
        parsed = []
        for line in text.splitlines():
            match = re.match(r'^(\s*)(0x[0-9a-fA-F]+)\s+"([^"]*)"', line)
            if match:
                parsed.append({"indent": len(match.group(1)), "id": match.group(2), "title": match.group(3)})
        attributes = [run(["xwininfo", "-id", item["id"]]) for item in parsed]
        title_rows = [item for item in parsed if item["indent"] == 0 and workbook.name in item["title"]
                      and "LibreOffice Calc" in item["title"]]
        disk_value = None
        with zipfile.ZipFile(workbook, "r") as archive:
            sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
            ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            value = sheet.find(".//s:c[@r='A1']/s:v", ns)
            disk_value = float(value.text) if value is not None else None
        after_hash = digest(workbook.read_bytes())
        raw = {
            "schema": "calc-doc-window-local-amd64-raw-v1",
            "allocation": ALLOCATION,
            "container_image_id": IMAGE_ID,
            "container_platform": "linux/amd64",
            "display": DISPLAY,
            "workbook": workbook.name,
            "workbook_sha256_before": before_hash,
            "workbook_sha256_after": after_hash,
            "live_a1_before": before_value,
            "live_a1_after": after_value,
            "persisted_a1_after_independent_xlsx_read": disk_value,
            "document_modified_unsaved": is_modified,
            "store_calls_after_initial_fixture_creation": 0,
            "soffice_version": run(["soffice", "--version"], timeout=10),
            "xwininfo_root_tree": tree,
            "root_tree_windows": parsed,
            "window_attribute_receipts": attributes,
            "document_title_matches": title_rows,
            "harness_completed": True,
            "scope": "one synthetic Calc document on local cached linux/amd64 Docker image; no Agent Interface runtime",
        }
        (OUT / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"allocation": ALLOCATION, "image_id": IMAGE_ID,
                          "document_title_matches": title_rows, "live_a1_after": after_value,
                          "persisted_a1": disk_value, "workbook_unchanged": before_hash == after_hash,
                          "harness_completed": True}, sort_keys=True))
        return 0
    finally:
        for proc in (soffice, xvfb):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
        xvfb_log.close()
        if soffice_log is not None:
            soffice_log.close()


if __name__ == "__main__":
    raise SystemExit(main())
