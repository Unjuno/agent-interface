import subprocess,unittest,json,os
from Xlib import display,XK
keeper=display.Display()
subprocess.run(['setxkbmap','-layout','us'],check=True)
d=display.Display()
result={'display':os.environ['DISPLAY'],'mapping':{n: {'code':d.keysym_to_keycode(XK.string_to_keysym(n)),'levels':[d.keycode_to_keysym(d.keysym_to_keycode(XK.string_to_keysym(n)),i) for i in range(4)]} for n in ('colon','apostrophe','underscore')}}
print(json.dumps(result),flush=True)
d.close()
from runtime.backends.x11_v1.test_integration import X11IntegrationTests
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(X11IntegrationTests))
raise SystemExit(not r.wasSuccessful())
