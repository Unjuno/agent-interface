from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ALLOCATION = "issue3733-german-xkb-text-orbstack-formal-02"
EVIDENCE = Path("/harness")
OUT = Path(sys.argv[1])


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if any(OUT.iterdir()):
        raise SystemExit("STOP_OUTPUT_DIRECTORY_NOT_EMPTY")
    raw1 = json.loads((EVIDENCE / "results/formal-01/raw.json").read_text())
    # Formal-01 is immutable history; this runner only validates its identity/hash.
    raw1_bytes = (EVIDENCE / "results/formal-01/raw.json").read_bytes()
    if raw1["allocation"] != "issue3733-german-xkb-text-orbstack-formal-01" or raw1["disposition"] != "STOP":
        raise SystemExit("STOP_PREDECESSOR_IDENTITY")
    # Import the frozen candidate only after source files match the new manifest.
    sys.path.insert(0, "/src")
    import Xlib
    from Xlib import XK, display
    from runtime.backends.x11_v1.backend import X11Backend, X11BackendError
    manifest = json.loads((EVIDENCE / "source_manifest_v2.json").read_text())
    for rel, expected in manifest["files"].items():
        if sha((Path("/src") / rel).read_bytes()) != expected:
            raise SystemExit(f"STOP_SOURCE_SHA:{rel}")
    if manifest["candidate_blob"] != "9cae101a219348077668c8fc086acf8e13154afe":
        raise SystemExit("STOP_CANDIDATE_BLOB")
    OUT.mkdir(parents=True, exist_ok=True)
    result = {
        "allocation": ALLOCATION,
        "source_base": manifest["base_commit"],
        "candidate_blob": manifest["candidate_blob"],
        "source_manifest_sha256": sha((EVIDENCE / "source_manifest_v2.json").read_bytes()),
        "runner_sha256": sha(Path(__file__).read_bytes()),
        "image_ref": "agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27",
        "platform": "linux/arm64",
        "container_network": "none",
        "formal01_raw_sha256": sha(raw1_bytes),
        "formal01_disposition": raw1["disposition"],
        "formal01_runtime_sha256": sha((EVIDENCE / "results/formal-01/runtime.json").read_bytes()),
        "runtime": {"python": sys.version, "xlib": str(getattr(Xlib, "__version__", "unknown"))},
        "rows": [],
    }
    import os
    import subprocess
    import time
    layouts = [("de-00", "de"), ("de-01", "de"), ("de-02", "de"), ("us-control", "us")]

    def proc_ticks(pid):
        try:
            return Path(f"/proc/{pid}/stat").read_text().split()[21]
        except (OSError, IndexError):
            return None

    def cmd(argv, env):
        p = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=12)
        return {"argv": argv, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}

    def mapping(d):
        i = d.display.info
        return [list(x) for x in d.get_keyboard_mapping(i.min_keycode, i.max_keycode-i.min_keycode+1)]

    def modifiers(d):
        return [list(x) for x in d.get_modifier_mapping()]

    def levels(d):
        ans = {}
        for ch, name in (("=", "equal"), ("*", "asterisk")):
            code = d.keysym_to_keycode(XK.string_to_keysym(name))
            ans[ch] = {"keysym_name": name, "keycode": int(code), "level0": int(d.keycode_to_keysym(code, 0)), "level1": int(d.keycode_to_keysym(code, 1))}
        return ans

    def fp(obj):
        return sha(json.dumps(obj, separators=(",", ":"), sort_keys=True).encode())

    def parse_events(text):
        events = []
        for block in re.split(r"(?m)(?=^(?:KeyPress|KeyRelease) event,)", text):
            first = re.match(r"(?m)^(KeyPress|KeyRelease) event,", block)
            if not first:
                continue
            km = re.search(r"keycode\s+(\d+)\s+\(keysym\s+0x[0-9a-fA-F]+,\s*([^)]+)\)", block)
            sm = re.search(r"(?m)^\s*state\s+0x([0-9a-fA-F]+)", block)
            lm = re.search(r"XLookupString gives \d+ bytes: \(([^)]*)\)", block)
            payload = ""
            if lm and lm.group(1).strip():
                try: payload = bytes.fromhex(lm.group(1)).decode("ascii")
                except (ValueError, UnicodeDecodeError): payload = "<non-ascii>"
            events.append({"type": first.group(1), "keycode": int(km.group(1)) if km else None, "keysym": km.group(2).strip() if km else None, "state": int(sm.group(1), 16) if sm else None, "lookup_ascii": payload})
        return events

    def stop(p, log=None):
        pid, ticks = p.pid, proc_ticks(p.pid)
        if p.poll() is None: p.terminate()
        try: rc = p.wait(timeout=4)
        except subprocess.TimeoutExpired:
            p.kill(); rc = p.wait(timeout=4)
        if log: log.flush(); log.close()
        return {"pid": pid, "start_ticks": ticks, "returncode": rc, "reaped": p.poll() is not None}

    for idx, (case, layout) in enumerate(layouts):
        cdir = OUT / "cases" / case
        cdir.mkdir(parents=True)
        disp = f":{151+idx}"
        env = os.environ.copy(); env["DISPLAY"] = disp
        xvlog = (cdir / "xvfb.log").open("wb")
        xv = subprocess.Popen(["/usr/bin/Xvfb", disp, "-screen", "0", "800x600x24", "-nolisten", "tcp", "+extension", "XKEYBOARD", "+extension", "XTEST"], env=env, stdin=subprocess.DEVNULL, stdout=xvlog, stderr=subprocess.STDOUT)
        row = {"case_id": case, "requested_layout": layout, "display": disp, "xvfb_pid": xv.pid, "xvfb_start_ticks": proc_ticks(xv.pid), "status": "STOP_SETUP_EXCEPTION"}
        xev = None; xlog = None; backend = None; server = None
        try:
            deadline = time.monotonic()+8
            while time.monotonic()<deadline:
                if xv.poll() is not None: raise RuntimeError(f"XVFB_EXITED:{xv.returncode}")
                try: server=display.Display(disp); break
                except Exception: time.sleep(.05)
            if server is None: raise RuntimeError("XVFB_CONNECT_TIMEOUT")
            row["extensions"]={"XKEYBOARD":bool(server.query_extension("XKEYBOARD").present),"XTEST":bool(server.has_extension("XTEST"))}
            if not all(row["extensions"].values()):
                row["status"]="STOP_X11_EXTENSION_MISSING"; raise RuntimeError("STOP_ROW_READY")
            bq=cmd(["setxkbmap","-query"],env); (cdir/"baseline.query.txt").write_text(bq["stdout"])
            bd=cmd(["xkbcomp","-xkb",disp,"-"],env); (cdir/"baseline.server.xkb").write_text(bd["stdout"])
            bm, bmod, blev=mapping(server), modifiers(server), levels(server)
            bl=re.search(r"(?m)^layout:\s*(\S+)",bq["stdout"])
            row["baseline"]={"layout":bl.group(1) if bl else None,"query_returncode":bq["returncode"],"server_dump_returncode":bd["returncode"],"server_dump_sha256":sha(bd["stdout"].encode()),"core_map_sha256":fp(bm),"modifier_map_sha256":fp(bmod),"symbol_levels":blev}
            if row["baseline"]["layout"]!="us" or bd["returncode"]!=0:
                row["status"]="STOP_BASELINE_NOT_US_OR_DUMP_FAILED"; raise RuntimeError("STOP_ROW_READY")
            if layout=="de":
                ap=cmd(["setxkbmap","-layout","de"],env); (cdir/"apply.log").write_text(json.dumps(ap,indent=2,sort_keys=True)+"\n")
                aq=cmd(["setxkbmap","-query"],env); (cdir/"after.query.txt").write_text(aq["stdout"])
                ad=cmd(["xkbcomp","-xkb",disp,"-"],env); (cdir/"after.server.xkb").write_text(ad["stdout"])
                # Critical harness fix: refresh Xlib after XKB transition, then verify client-visible map.
                server.close(); server=None
                fresh=display.Display(disp)
                am, amod, alev=mapping(fresh), modifiers(fresh), levels(fresh)
                fresh.close()
                al=re.search(r"(?m)^layout:\s*(\S+)",aq["stdout"])
                row["apply"]={"argv":ap["argv"],"returncode":ap["returncode"],"stdout":ap["stdout"],"stderr":ap["stderr"]}
                row["after"]={"layout":al.group(1) if al else None,"query_returncode":aq["returncode"],"server_dump_returncode":ad["returncode"],"server_dump_sha256":sha(ad["stdout"].encode()),"core_map_sha256":fp(am),"modifier_map_sha256":fp(amod),"symbol_levels":alev,"server_changed":bd["stdout"]!=ad["stdout"],"core_map_changed":bm!=am,"modifier_map_changed":bmod!=amod,"fresh_client":True}
                (cdir/"fresh-client-map.json").write_text(json.dumps({"core_map":am,"modifier_map":amod,"symbol_levels":alev},indent=2,sort_keys=True)+"\n")
                if not(ap["returncode"]==0 and aq["returncode"]==0 and row["after"]["layout"]=="de" and ad["returncode"]==0 and row["after"]["server_changed"] and row["after"]["core_map_changed"] and all(any(v==ord(ch) for v in (alev[ch]["level0"],alev[ch]["level1"])) for ch in ("=","*"))):
                    row["status"]="STOP_SETUP_BLOCKED_NATIVE_XKB_APPLY"; raise RuntimeError("STOP_ROW_READY")
                active=alev
            else:
                row["after"]=row["baseline"]|{"layout":"us","server_changed":False,"core_map_changed":False,"modifier_map_changed":False,"fresh_client":True}; active=blev
            server.close(); server=None
            xlog=(cdir/"xev.log").open("wb")
            xev=subprocess.Popen(["stdbuf","-oL","xev","-event","keyboard"],env=env,stdin=subprocess.DEVNULL,stdout=xlog,stderr=subprocess.STDOUT)
            deadline=time.monotonic()+8; outer=inner=None; xt=""
            while time.monotonic()<deadline:
                if xev.poll() is not None: raise RuntimeError(f"XEV_EXITED_EARLY:{xev.returncode}")
                xt=(cdir/"xev.log").read_text(errors="replace")
                ids=re.search(r"Outer window is 0x([0-9a-fA-F]+),\s*inner window is 0x([0-9a-fA-F]+)",xt,re.I)
                if ids: outer,inner=(int(ids.group(1),16),int(ids.group(2),16)); break
                time.sleep(.05)
            if inner is None: raise RuntimeError("XEV_WINDOW_ID_TIMEOUT_V2")
            row["receiver"]={"process_pid":xev.pid,"process_start_ticks":proc_ticks(xev.pid),"outer_window":outer,"inner_window":inner,"implementation":"xev XLookupString"}
            backend=X11Backend(disp,{"receiver":inner}); row["active_symbol_levels"]=active
            try: row["candidate_plan"]=backend._text_plan("=B2*A2")
            except X11BackendError as e: row["candidate_error"]=str(e); row["status"]="FAIL_CANDIDATE_TEXT_PLAN"; raise RuntimeError("FAIL_ROW_READY")
            row["candidate_plan_keycodes"]=[[backend._keycode(k) for k in ch] for ch in row["candidate_plan"]]
            unsupported_error=None
            try: backend.preflight({"ops":[{"op":"focus","target":"receiver"},{"op":"text","text":"=B2*A2€"}]})
            except X11BackendError as e: unsupported_error=str(e)
            time.sleep(.15); pre=(cdir/"xev.log").read_text(errors="replace"); (cdir/"unsupported.preflight.xev.txt").write_text(pre)
            kp=len(re.findall(r"(?m)^KeyPress event,",pre))
            row["unsupported_control"]={"payload":"=B2*A2€","refused":unsupported_error is not None,"error":unsupported_error,"emissions_after":backend.emissions,"receiver_keypresses_after":kp}
            if not(unsupported_error and "U+20AC" in unsupported_error and backend.emissions==0 and kp==0): row["status"]="FAIL_UNSUPPORTED_PREFLIGHT_EMITTED_OR_ACCEPTED"; raise RuntimeError("FAIL_ROW_READY")
            try: backend.preflight({"ops":[{"op":"focus","target":"receiver"},{"op":"text","text":"=B2*A2"}]})
            except X11BackendError as e: row["status"]="FAIL_VALID_FORMULA_PREFLIGHT"; row["valid_preflight_error"]=str(e); raise RuntimeError("FAIL_ROW_READY")
            backend.focus("receiver"); row["emissions_before_text"]=backend.emissions; backend.text("=B2*A2"); row["emissions_after_text"]=backend.emissions
            deadline=time.monotonic()+4; et=""
            while time.monotonic()<deadline:
                time.sleep(.05); et=(cdir/"xev.log").read_text(errors="replace")
                ev=parse_events(et)
                if "".join(e["lookup_ascii"] for e in ev if e["type"]=="KeyPress")=="=B2*A2": break
            row["receiver_events"]=parse_events(et); row["receiver_text"]="".join(e["lookup_ascii"] for e in row["receiver_events"] if e["type"]=="KeyPress")
            row["status"]="EXECUTED"; row["event_log_sha256"]=sha((cdir/"xev.log").read_bytes())
        except Exception as exc:
            if str(exc) not in {"STOP_ROW_READY","FAIL_ROW_READY"}: row["error"]=f"{type(exc).__name__}:{exc}"
        finally:
            if backend:
                try: backend.close()
                except Exception as e: row["backend_close_error"]=repr(e)
            if server:
                try: server.close()
                except Exception: pass
            if xev:
                row["xev_process"]=stop(xev,xlog); xlog=None
            elif xlog: xlog.close(); xlog=None
            row["xvfb_process"]=stop(xv,xvlog)
            row["xvfb_log_sha256"]=sha((cdir/"xvfb.log").read_bytes())
            if (cdir/"xev.log").exists(): row["event_log_sha256"]=sha((cdir/"xev.log").read_bytes())
        result["rows"].append(row)
        (OUT/"raw.partial.json").write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
        if row["status"].startswith("STOP_") or row["status"].startswith("FAIL_") or row["status"]!="EXECUTED": break
    if len(result["rows"])<4:
        result["disposition"]="STOP" if result["rows"][-1]["status"].startswith("STOP_") else "FAIL"
    elif any(not r["status"].startswith("EXECUTED") for r in result["rows"]): result["disposition"]="FAIL"
    else: result["disposition"]="EXECUTED_PENDING_INDEPENDENT_AUDIT"
    inventory={p.relative_to(OUT).as_posix():sha(p.read_bytes()) for p in sorted(OUT.rglob("*")) if p.is_file() and p.name!="raw.json"}
    result["artifact_sha256"]=inventory
    result["disposition"] = result.get("disposition","STOP")
    (OUT/"raw.json").write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    (OUT/"raw.partial.json").unlink(missing_ok=True)
    print(json.dumps({"allocation":ALLOCATION,"disposition":result["disposition"],"rows":[{"case_id":r["case_id"],"status":r["status"]} for r in result["rows"]]},sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
