import json, os, signal, subprocess, tempfile, time
from pathlib import Path
from PIL import ImageGrab
from Xlib import display

out = Path(__file__).resolve().parent / "raw" / "preflight"
chrome = "/home/user/.cache/agent-interface-live-caller-20261021/browsers/chromium-1248/chrome-linux64/chrome"
libs = "/home/user/.cache/agent-interface-live-caller-20261021/linux-libs/rootfs/usr/lib/x86_64-linux-gnu"
result = {"preflight_id":"private-wsl2-chromium-x11-visible-capture-20261021-r01",
          "display":os.environ.get("DISPLAY"), "screen_expected":[1024,768]}
server = None
browser = None
try:
    server = subprocess.Popen(["Xvfb", ":93", "-screen", "0", "1024x768x24", "-ac", "-nolisten", "tcp"],
        stdout=open(out/"xvfb.log","wb"), stderr=subprocess.STDOUT, start_new_session=True)
    os.environ["DISPLAY"] = ":93"
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        try:
            d=display.Display(":93"); d.close(); break
        except Exception: time.sleep(.05)
    else: raise TimeoutError("private Xvfb did not become ready")
    with tempfile.TemporaryDirectory(prefix="chromium-preflight-") as tmp:
        html=Path(tmp)/"preflight.html"
        html.write_text("<!doctype html><title>AI-CONTROL-BROWSER-PREFLIGHT</title><body style='background:#abcdef'><h1>Capture ready</h1></body>", encoding="utf-8")
        env=dict(os.environ, LD_LIBRARY_PATH=libs)
        browser=subprocess.Popen([chrome,"--no-sandbox","--disable-gpu","--disable-dev-shm-usage",
            "--no-first-run","--no-default-browser-check","--disable-background-networking",
            "--disable-component-update","--password-store=basic","--window-size=1024,768",
            "--window-position=0,0",f"--user-data-dir={tmp}/profile",f"--app=file://{html}"],
            stdout=subprocess.DEVNULL,stderr=open(out/"chromium-stderr.txt","wb"),env=env,start_new_session=True)
        d=display.Display(":93"); root=d.screen().root; found=None
        deadline=time.monotonic()+15
        while time.monotonic()<deadline and found is None:
            for w in root.query_tree().children:
                try:
                    attrs=w.get_attributes(); g=w.get_geometry()
                    title=w.get_wm_name()
                    if attrs.map_state==2 and g.width>600 and g.height>400:
                        found={"window_id":w.id,"title":title,"width":g.width,"height":g.height}
                        break
                except Exception: pass
            time.sleep(.1)
        if found is None: raise TimeoutError("no mapped Chromium app window found")
        time.sleep(.5)
        image=ImageGrab.grab(xdisplay=":93").convert("RGB")
        image.save(out/"chromium-screen.png")
        result.update(status="PASS_CHROMIUM_WINDOW_AND_X11_CAPTURE", chromium_version=subprocess.check_output([chrome,"--version"],env=env,text=True).strip(),
                      window=found, screenshot_size=list(image.size), sample_rgb=list(image.getpixel((20,20))),
                      xvfb_pid=server.pid,browser_pid=browser.pid,screenshot="chromium-screen.png")
        d.close()
except Exception as error:
    result.update(status="FAIL_PREFLIGHT",error_type=type(error).__name__,error=repr(error))
finally:
    for proc in (browser,server):
        if proc is not None and proc.poll() is None:
            try: os.killpg(proc.pid,signal.SIGTERM)
            except ProcessLookupError: pass
            try: proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                try: os.killpg(proc.pid,signal.SIGKILL)
                except ProcessLookupError: pass
                proc.wait()
    result["browser_exitcode"]=None if browser is None else browser.returncode
    result["xvfb_exitcode"]=None if server is None else server.returncode
    (out/"result.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
raise SystemExit(0 if result.get("status")=="PASS_CHROMIUM_WINDOW_AND_X11_CAPTURE" else 1)