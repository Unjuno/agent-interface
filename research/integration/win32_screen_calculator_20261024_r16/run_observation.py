import asyncio, base64, ctypes, hashlib, json, re, subprocess, sys
from ctypes import wintypes
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]; PACKET=Path(__file__).resolve().parent
sys.path.insert(0,str(REPO))
from runtime.cli_v1.mcp_server import create_server
TARGET_NAME="calculator"; TARGET_HWND=55117672; TARGET_PID=35132; EXPECTED="1043"; REGION=[48, 32, 320, 533]
def write_json(path,obj): Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def response_text(reply,label):
 texts=[]; images=0
 for block in reply.content:
  if getattr(block,"type",None)=="text": texts.append(block.text)
  elif getattr(block,"type",None)=="image":
   (PACKET/"run"/f"{label}-image-{images:02d}.png").write_bytes(base64.b64decode(block.data)); images+=1
 (PACKET/"run"/f"{label}-raw.txt").write_text("\n".join(texts),encoding="utf-8")
 if not texts: raise RuntimeError(label+" returned no text")
 return json.loads(texts[0])
def read_uia():
 cmd=["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",str(PACKET/"uia_read.ps1"),"-Hwnd",str(TARGET_HWND),"-ExpectedDisplay","","-TimeoutMs","0"]
 cp=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=10)
 raw={"argv":cmd,"returncode":cp.returncode,"stdout":cp.stdout,"stderr":cp.stderr}
 if cp.returncode: raise RuntimeError("UIA preflight failed: "+json.dumps(raw,ensure_ascii=False))
 raw["parsed"]=json.loads(cp.stdout.strip()); return raw
def window_state():
 u=ctypes.WinDLL("user32",use_last_error=True)
 u.IsWindow.argtypes=[wintypes.HWND];u.IsWindow.restype=wintypes.BOOL
 u.IsWindowVisible.argtypes=[wintypes.HWND];u.IsWindowVisible.restype=wintypes.BOOL
 u.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)];u.GetWindowThreadProcessId.restype=wintypes.DWORD
 u.GetForegroundWindow.restype=wintypes.HWND
 u.GetAncestor.argtypes=[wintypes.HWND,wintypes.UINT];u.GetAncestor.restype=wintypes.HWND
 def hv(v): return int(ctypes.cast(v,ctypes.c_void_p).value or 0)
 def pid(hwnd):
  d=wintypes.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(d));return int(d.value)
 fg=hv(u.GetForegroundWindow());root=hv(u.GetAncestor(fg,2)) if fg else 0
 return {"target_is_window":bool(u.IsWindow(TARGET_HWND)),"target_visible":bool(u.IsWindowVisible(TARGET_HWND)),"target_pid":pid(TARGET_HWND) if u.IsWindow(TARGET_HWND) else None,"foreground_root_hwnd":root,"target_is_foreground_root":root==TARGET_HWND}
def client_region():
 u=ctypes.WinDLL("user32",use_last_error=True)
 class RECT(ctypes.Structure): _fields_=[("left",ctypes.c_long),("top",ctypes.c_long),("right",ctypes.c_long),("bottom",ctypes.c_long)]
 class POINT(ctypes.Structure): _fields_=[("x",ctypes.c_long),("y",ctypes.c_long)]
 u.GetClientRect.argtypes=[wintypes.HWND,ctypes.POINTER(RECT)];u.GetClientRect.restype=wintypes.BOOL
 u.ClientToScreen.argtypes=[wintypes.HWND,ctypes.POINTER(POINT)];u.ClientToScreen.restype=wintypes.BOOL
 h=wintypes.HWND(TARGET_HWND);r=RECT();pt=POINT(0,0)
 if not u.GetClientRect(h,ctypes.byref(r)) or not u.ClientToScreen(h,ctypes.byref(pt)): raise OSError(ctypes.get_last_error(),"client geometry failed")
 return [pt.x,pt.y,r.right-r.left,r.bottom-r.top]
async def main():
 run=PACKET/"run"; before=read_uia(); state=window_state(); region_now=client_region()
 write_json(run/"uia-preflight.json",before);write_json(run/"win32-preflight.json",state);write_json(run/"client-region.json",{"region":region_now})
 if before["parsed"]["display_digits"]!=EXPECTED: raise RuntimeError("STOP before observation: UIA display changed")
 if state["target_pid"]!=TARGET_PID or not state["target_is_window"] or not state["target_visible"] or not state["target_is_foreground_root"]: raise RuntimeError("STOP before observation: target identity/focus changed")
 if region_now!=REGION: raise RuntimeError("STOP before observation: client physical region changed")
 server=create_server({TARGET_NAME:TARGET_HWND},str(run/"server"),session_mode="supervised-win32")
 close=None
 try:
  reply=await server.call_tool("interface_observe",{"target":TARGET_NAME,"frame":"screen_physical_px","region":REGION,"compact":False,"report_refs":False})
  observation=response_text(reply,"observation")
  write_json(run/"observation-parsed.json",observation)
 finally:
  try:
   close=response_text(await server.call_tool("interface_close",{}),"close")
   write_json(run/"close.json",close)
  except BaseException as error: write_json(run/"close-error.json",{"error":repr(error)})
 report=(observation.get("receipt") or {}).get("report") or {}
 print(json.dumps({"attempt_id":'win32-screen-calculator-observation-20261024-r16-537c22e9',"observation_status":report.get("status"),"frame":(report.get("observation") or {}).get("frame"),"generation":report.get("target_generation"),"input_dispatched":report.get("input_dispatched"),"close_status":(close or {}).get("status"),"call_count":((close or {}).get("session") or {}).get("call_count")},ensure_ascii=False,sort_keys=True))
if __name__=="__main__": asyncio.run(main())
