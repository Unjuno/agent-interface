#!/usr/bin/env python3
"""One-run XTEST two-client overlapping-hold routing probe."""
import argparse, ctypes as C, hashlib, json, os, platform, sys, time, traceback
from pathlib import Path

class XDeviceInfo(C.Structure):
    _fields_ = [("id", C.c_ulong), ("type", C.c_ulong), ("name", C.c_char_p),
                ("num_classes", C.c_int), ("use", C.c_int), ("inputclassinfo", C.c_void_p)]
class XKeyEvent(C.Structure):
    _fields_ = [("type", C.c_int), ("serial", C.c_ulong), ("send_event", C.c_int),
                ("display", C.c_void_p), ("window", C.c_ulong), ("root", C.c_ulong),
                ("subwindow", C.c_ulong), ("time", C.c_ulong), ("x", C.c_int),
                ("y", C.c_int), ("x_root", C.c_int), ("y_root", C.c_int),
                ("state", C.c_uint), ("keycode", C.c_uint), ("same_screen", C.c_int)]
class XEvent(C.Union):
    _fields_ = [("type", C.c_int), ("xkey", XKeyEvent), ("pad", C.c_long * 24)]
class XErrorEvent(C.Structure):
    _fields_ = [("type", C.c_int), ("display", C.c_void_p), ("resourceid", C.c_ulong),
                ("serial", C.c_ulong), ("error_code", C.c_ubyte),
                ("request_code", C.c_ubyte), ("minor_code", C.c_ubyte)]
ErrorHandler = C.CFUNCTYPE(C.c_int, C.c_void_p, C.POINTER(XErrorEvent))
errors = []
def on_x_error(_display, ptr):
    e = ptr.contents
    errors.append({"resourceid": int(e.resourceid), "serial": int(e.serial),
                   "error_code": int(e.error_code), "request_code": int(e.request_code),
                   "minor_code": int(e.minor_code)})
    return 0
handler = ErrorHandler(on_x_error)

def setup_lib(lib, funcs):
    for name, (restype, argtypes) in funcs.items():
        f = getattr(lib, name); f.restype = restype; f.argtypes = argtypes


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); args = ap.parse_args()
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    raw = {"schema":"x11-xtest-device-cross-client-raw-a01-v1", "allocation":"X11-XTEST-DEVICE-CROSS-CLIENT-A01-20261005",
           "display":os.environ.get("DISPLAY"), "platform":platform.platform(), "python":sys.version,
           "started_ns":time.time_ns(), "candidate_exit":None, "x_errors":errors, "routes":[], "cleanup":{},"api_calls":[]}
    status = 1; displays=[]; devices=[]; client=None; observer=None; win=0; keycode=0
    try:
        if raw["display"] != ":87": raise RuntimeError("unexpected DISPLAY; frozen server is :87")
        x11=C.CDLL("libX11.so.6"); xi=C.CDLL("libXi.so.6"); xt=C.CDLL("libXtst.so.6")
        p=C.c_void_p; u=C.c_ulong; i=C.c_int; ui=C.c_uint
        setup_lib(x11, {
          "XOpenDisplay":(p,[C.c_char_p]), "XCloseDisplay":(i,[p]), "XSetErrorHandler":(C.c_void_p,[ErrorHandler]),
          "XDefaultScreen":(i,[p]), "XRootWindow":(u,[p,i]),
          "XCreateSimpleWindow":(u,[p,u,i,i,ui,ui,ui,u,u]), "XSelectInput":(i,[p,u,u]),
          "XMapWindow":(i,[p,u]), "XSetInputFocus":(i,[p,u,i,u]), "XSync":(i,[p,i]),
          "XPending":(i,[p]), "XNextEvent":(i,[p,C.POINTER(XEvent)]),
          "XQueryKeymap":(i,[p,C.c_char_p]), "XKeysymToKeycode":(ui,[p,u]), "XDestroyWindow":(i,[p,u])})
        setup_lib(xi,{"XListInputDevices":(C.POINTER(XDeviceInfo),[p,C.POINTER(i)]),
                      "XOpenDevice":(p,[p,u]), "XCloseDevice":(i,[p,p]), "XFreeDeviceList":(None,[C.POINTER(XDeviceInfo)])})
        setup_lib(xt,{"XTestFakeKeyEvent":(i,[p,ui,i,u]),
                      "XTestFakeDeviceKeyEvent":(i,[p,p,ui,i,C.POINTER(i),i,u])})
        x11.XSetErrorHandler(handler)
        client=x11.XOpenDisplay(None); observer=x11.XOpenDisplay(None); a=x11.XOpenDisplay(None); b=x11.XOpenDisplay(None)
        displays=[client,observer,a,b]
        if any(not d for d in displays): raise RuntimeError("XOpenDisplay failed")
        raw["client_connections"]={"receiver":True,"observer":True,"A":True,"B":True,"A_and_B_distinct":int(a)!=int(b)}
        if not raw["client_connections"]["A_and_B_distinct"]: raise RuntimeError("A and B display connections unexpectedly alias")
        count=i(0); info=xi.XListInputDevices(a,C.byref(count))
        if not info: raise RuntimeError("XListInputDevices failed")
        found=[]
        for n in range(count.value):
            entry=info[n]; name=entry.name.decode("utf-8","replace") if entry.name else ""
            if "XTEST" in name.upper() and "KEYBOARD" in name.upper(): found.append((int(entry.id),name))
        xi.XFreeDeviceList(info)
        raw["devices_found"]=found
        if len(found)!=1: raise RuntimeError("expected exactly one server XTEST keyboard, found %r"%(found,))
        devid,devname=found[0]
        da=xi.XOpenDevice(a,devid); db=xi.XOpenDevice(b,devid); devices=[(a,da),(b,db)]
        if not da or not db: raise RuntimeError("XOpenDevice failed for shared XTEST keyboard")
        raw["device_handles_open"]={"A":True,"B":True,"same_server_device_id":devid}
        screen=x11.XDefaultScreen(client); root=x11.XRootWindow(client,screen)
        win=x11.XCreateSimpleWindow(client,root,0,0,120,80,0,0,0)
        if not win: raise RuntimeError("XCreateSimpleWindow failed")
        x11.XSelectInput(client,win,3); x11.XMapWindow(client,win); x11.XSetInputFocus(client,win,2,0); x11.XSync(client,0)
        keycode=int(x11.XKeysymToKeycode(client,ord("w")))
        if keycode==0: raise RuntimeError("XKeysymToKeycode('w') returned zero")
        raw.update({"device_id":devid,"device_name":devname,"window_id":int(win),"key":"w","keycode":keycode})
        def sample():
            buf=C.create_string_buffer(32)
            if x11.XQueryKeymap(observer,buf)!=1: raise RuntimeError("XQueryKeymap failed")
            return bool(buf.raw[keycode//8] & (1 << (keycode%8)))
        raw["initial_keymap_down"]=sample()
        if raw["initial_keymap_down"]: raise RuntimeError("initial XQueryKeymap state is already down")
        def events():
            x11.XSync(client,0); got=[]
            while x11.XPending(client):
                ev=XEvent(); x11.XNextEvent(client,C.byref(ev))
                if ev.type in (2,3):
                    got.append({"type":"KeyPress" if ev.type==2 else "KeyRelease","window_id":int(ev.xkey.window),
                                "keycode":int(ev.xkey.keycode),"serial":int(ev.xkey.serial),"time":int(ev.xkey.time)})
            return got
        def route(kind):
            before=len(errors); result={"route":kind,"steps":[],"x_errors":[]}
            raw["routes"].append(result)
            def invoke(who,down):
                d=a if who=="A" else b
                if kind=="core":
                    api="XTestFakeKeyEvent"; rc=xt.XTestFakeKeyEvent(d,keycode,int(down),0)
                else:
                    api="XTestFakeDeviceKeyEvent"; rc=xt.XTestFakeDeviceKeyEvent(d,da if who=="A" else db,keycode,int(down),None,0,0)
                raw["api_calls"].append({"route":kind,"actor":who,"edge":"DOWN" if down else "UP","api":api,"return_code":int(rc)})
                x11.XSync(d,0)
                if rc==0: raise RuntimeError("%s %s request returned 0"%(who,"DOWN" if down else "UP"))
            for who,down in (("A",True),("B",True),("A",False),("B",False)):
                invoke(who,down)
                result["steps"].append({"actor":who,"edge":"DOWN" if down else "UP","keymap_down":sample(),"core_events":events()})
            result["x_errors"]=errors[before:]
            return result
        route("core")
        if sample(): raise RuntimeError("core route failed to return keymap to neutral")
        if events(): raw["unexpected_between_routes"]=events()
        route("device")
        if sample(): raise RuntimeError("device route failed to return keymap to neutral")
        raw["final_core_events"]=events()
        if errors: raise RuntimeError("X protocol errors were observed")
        raw["completed_ns"]=time.time_ns(); raw["status"]="CANDIDATE_COMPLETE"; status=0
    except BaseException as exc:
        raw["status"]="STOP_CANDIDATE_ERROR"; raw["exception"]={"type":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc()}
        raw["completed_ns"]=time.time_ns()
    finally:
        try:
            if client and win: x11.XDestroyWindow(client,win); x11.XSync(client,0)
            for d,dev in devices:
                if dev: xi.XCloseDevice(d,dev); x11.XSync(d,0)
            for d in displays:
                if d: x11.XCloseDisplay(d)
        except BaseException as exc:
            raw["cleanup"]["exception"]={"type":type(exc).__name__,"message":str(exc)}; status=1
        raw["x_errors"]=errors
        raw["cleanup"]["displays_closed"]=len(displays)
        raw["candidate_exit"]=status
        raw["finished_ns"]=time.time_ns()
        data=(json.dumps(raw,sort_keys=True,indent=2)+"\n").encode()
        out.write_bytes(data)
        print(json.dumps({"raw":str(out),"sha256":hashlib.sha256(data).hexdigest(),"status":raw["status"],"candidate_exit":status},sort_keys=True))
    return status

if __name__=="__main__": raise SystemExit(main())





