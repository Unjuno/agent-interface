import os,subprocess,time,json
from Xlib import display
from PIL import Image
processes=[]
result={}
try:
 processes.append(subprocess.Popen(['Xvfb',':97','-screen','0','1280x800x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
 os.environ['DISPLAY']=':97'
 deadline=time.monotonic()+5
 while True:
  try: d=display.Display(':97'); break
  except Exception:
   if time.monotonic()>deadline: raise
   time.sleep(.1)
 processes.append(subprocess.Popen(['openbox'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
 processes.append(subprocess.Popen(['chromium','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--no-first-run','--disable-background-networking','--user-data-dir=/tmp/gui-prerequisite','--window-size=1000,700','data:text/html,<title>WSLC_GUI_57</title><p>Chromium GUI prerequisite</p>'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
 deadline=time.monotonic()+10
 names=[]
 while time.monotonic()<deadline:
  names=[w.get_wm_name() for w in d.screen().root.query_tree().children]
  if any('WSLC_GUI_57' in (n or '') for n in names): break
  time.sleep(.2)
 root=d.screen().root
 raw=root.get_image(0,0,1280,800,2,0xffffffff)
 frame=Image.frombytes('RGB',(1280,800),raw.data,'raw','BGRX')
 result={'window_titles':names,'chromium_window_found':any('WSLC_GUI_57' in (n or '') for n in names),'screen_size':frame.size,'distinct_colors':len(frame.getcolors(1280*800) or [])}
 print(json.dumps(result))
 d.close()
finally:
 for p in reversed(processes):
  p.terminate()
  try: p.wait(timeout=5)
  except subprocess.TimeoutExpired: p.kill(); p.wait(timeout=5)
raise SystemExit(0 if result.get('chromium_window_found') and result['distinct_colors']>20 else 1)
