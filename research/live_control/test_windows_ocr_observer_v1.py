"""Offline checks for exact-token matching and the native Windows OCR worker."""

import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request
import unittest
from pathlib import Path

from research.live_control.windows_ocr_observer_v1 import (
    WindowsOcrObserver,
    exact_token_present,
    exact_token_state,
)


class ExactTokenTests(unittest.TestCase):
    def test_match_requires_the_complete_token(self):
        self.assertTrue(exact_token_present("Value: t991025-1", "t991025-1"))
        self.assertFalse(exact_token_present("Value: xt991025-1", "t991025-1"))
        self.assertFalse(exact_token_present("Value: t991025-10", "t991025-1"))
        self.assertFalse(exact_token_present("Value: t991025-2", "t991025-1"))
        self.assertEqual(exact_token_state("", "t991025-1"), "unknown")
        self.assertFalse(exact_token_state("Value: t991025-2", "t991025-1"))

    def test_invalid_expected_token_is_rejected(self):
        for token in ("", 7, None):
            with self.subTest(token=token):
                with self.assertRaises(ValueError):
                    exact_token_present("text", token)
                with self.assertRaises(ValueError):
                    exact_token_state("", token)


@unittest.skipUnless(os.name == "nt", "native OCR integration requires Windows")
class NativeOcrTests(unittest.TestCase):
    def test_persistent_worker_reads_exact_ascii_token_and_negative_control(self):
        from PIL import Image, ImageDraw, ImageFont

        with tempfile.TemporaryDirectory(prefix="interface-ocr-") as directory:
            image_path = Path(directory) / "token.png"
            image = Image.new("RGB", (640, 240), "white")
            draw = ImageDraw.Draw(image)
            font_path = Path(os.environ["WINDIR"]) / "Fonts" / "arial.ttf"
            draw.text((30, 40), "Enter token: t991025-1",
                      font=ImageFont.truetype(str(font_path), 36), fill="black")
            image.save(image_path)

            with WindowsOcrObserver() as observer:
                first = observer.recognize(image_path, region=(20, 30, 400, 80),
                                           scale=2)
                second = observer.recognize(image_path, region=(20, 30, 400, 80),
                                            scale=4)

            self.assertEqual(first["status"], "ok")
            self.assertTrue(exact_token_present(first["text"], "t991025-1"),
                            first["text"])
            self.assertFalse(exact_token_present(first["text"], "t991025-2"))
            self.assertEqual(first["language"], second["language"])
            self.assertTrue(first["text"])
            self.assertGreater(first["elapsed_ns"], 0)

    def test_invalid_region_and_scale_fail_before_worker_input(self):
        if os.name != "nt":
            self.skipTest("native OCR integration requires Windows")
        from PIL import Image

        with tempfile.TemporaryDirectory(prefix="interface-ocr-validation-") as directory:
            image_path = Path(directory) / "blank.png"
            Image.new("RGB", (20, 20), "white").save(image_path)
            with WindowsOcrObserver() as observer:
                for kwargs in ({"region": (0, 0, 30, 30)}, {"scale": 9},
                               {"region": (0, 0, True, 4)}):
                    with self.subTest(kwargs=kwargs):
                        with self.assertRaises(ValueError):
                            observer.recognize(image_path, **kwargs)


@unittest.skipUnless(os.name == "nt", "Edge OCR integration requires Windows")
class BrowserFrameOcrTests(unittest.TestCase):
    def test_cropped_edge_form_frame_contains_exact_value(self):
        edge = Path(os.environ.get("ProgramFiles(x86)",
                                   r"C:\Program Files (x86)")) / "Microsoft" / \
            "Edge" / "Application" / "msedge.exe"
        node = shutil.which("node.exe") or shutil.which("node")
        if not edge.is_file() or node is None:
            self.skipTest("Edge and Node.js are required for browser-frame OCR")

        node_script = r'''const fs=require('fs');const [pageWs,browserWs,url,out]=process.argv.slice(1);let seq=0;const pending=new Map();const ws=new WebSocket(pageWs);function rpc(method,params={}){const id=++seq;return new Promise((resolve,reject)=>{pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});}ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result||{});}});ws.addEventListener('open',async()=>{try{let resolveLoad;const loaded=new Promise(r=>resolveLoad=r);const f=e=>{if(JSON.parse(e.data).method==='Page.loadEventFired'){ws.removeEventListener('message',f);resolveLoad();}};ws.addEventListener('message',f);await rpc('Page.enable');await rpc('Emulation.setDeviceMetricsOverride',{width:756,height:488,deviceScaleFactor:1,mobile:false});await rpc('Page.navigate',{url});await Promise.race([loaded,new Promise(r=>setTimeout(r,5000))]);const s=await rpc('Page.captureScreenshot',{format:'png',fromSurface:true});fs.writeFileSync(out,Buffer.from(s.data,'base64'));ws.close();const b=new WebSocket(browserWs);b.addEventListener('open',()=>b.send(JSON.stringify({id:1,method:'Browser.close'})));setTimeout(()=>process.exit(0),500);}catch(e){console.error(String(e));process.exit(2);}});'''
        page_html = (
            '<!doctype html><meta charset="utf-8">'
            '<style>body{font:16px Arial;margin:100px}label{display:block}'
            'input{font:16px Arial;width:220px}</style>'
            '<label>Value <input value="t991025-1"></label><button>Save</button>')

        with tempfile.TemporaryDirectory(
                prefix="interface-edge-frame-ocr-",
                dir=str(Path(__file__).resolve().parent)) as directory:
            root = Path(directory)
            profile = root / "profile"
            page = root / "form.html"
            image = root / "form.png"
            page.write_text(page_html, encoding="utf-8")
            edge_process = subprocess.Popen([
                str(edge), "--headless=new", "--disable-gpu", "--no-first-run",
                "--no-default-browser-check", "--remote-debugging-address=127.0.0.1",
                "--remote-debugging-port=0", "--remote-allow-origins=*",
                f"--user-data-dir={profile}", "about:blank"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            port_file = profile / "DevToolsActivePort"
            deadline = time.monotonic() + 12
            version = None
            while time.monotonic() < deadline:
                if port_file.exists():
                    try:
                        port = int(port_file.read_text(encoding="ascii").splitlines()[0])
                        version = json.load(urllib.request.urlopen(
                            f"http://127.0.0.1:{port}/json/version", timeout=1))
                        break
                    except (OSError, ValueError, json.JSONDecodeError):
                        pass
                time.sleep(0.1)
            self.assertIsNotNone(version, "isolated Edge DevTools endpoint did not start")

            targets = json.load(urllib.request.urlopen(
                f"http://127.0.0.1:{port}/json/list", timeout=2))
            target = next(row for row in targets if row.get("type") == "page")
            captured = subprocess.run([
                node, "-e", node_script, target["webSocketDebuggerUrl"],
                version["webSocketDebuggerUrl"], page.as_uri(), str(image)],
                capture_output=True, text=True, timeout=12)
            if edge_process.poll() is None:
                edge_process.wait(timeout=3)
            else:
                edge_process.wait()
            self.assertEqual(captured.returncode, 0, captured.stderr)
            self.assertTrue(image.is_file())

            with WindowsOcrObserver(timeout_seconds=12) as observer:
                result = observer.recognize(image, region=(125, 80, 355, 70),
                                            scale=2)

            self.assertEqual(result["status"], "ok")
            self.assertTrue(exact_token_present(result["text"], "t991025-1"),
                            result["text"])
            self.assertFalse(exact_token_present(result["text"], "t991025-2"),
                             result["text"])


if __name__ == "__main__":
    unittest.main()
