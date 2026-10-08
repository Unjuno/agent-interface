"""Private X11 test adapter. Not the project's production Executor."""
import os
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
import numpy as np
from PIL import ImageGrab
from Xlib import X, display
from Xlib.ext import xtest
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent


@contextmanager
def environment():
    proc=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','1024x768x24',
                           '-nolisten','tcp','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    name=':'+proc.stdout.readline().strip()
    if name==':':
        raise RuntimeError('Xvfb failed')
    auth=tempfile.TemporaryDirectory(prefix='commit-guard-auth-')
    authfile=Path(auth.name)/'Xauthority';authfile.touch()
    old=os.environ.get('XAUTHORITY');os.environ['XAUTHORITY']=str(authfile)
    d=None
    try:
        d=display.Display(name)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=False,
                env={**os.environ,'DISPLAY':name},args=['--no-sandbox','--disable-dev-shm-usage',
                '--window-position=0,0','--window-size=1024,768','--force-device-scale-factor=1'])
            context=browser.new_context(viewport={'width':800,'height':600},device_scale_factor=1)
            page=context.new_page();page.set_content((HERE/'fixture.html').read_text())
            page.bring_to_front();cdp=context.new_cdp_session(page)
            cdp.send('Accessibility.enable');page.wait_for_timeout(100)
            rgb=np.array(ImageGrab.grab(xdisplay=name).convert('RGB'))
            yy,xx=np.where(np.all(rgb==(250,0,250),axis=2))
            if len(xx)!=16:
                raise RuntimeError('marker calibration failed')
            origin=(int(xx.min()),int(yy.min()))
            layout=cdp.send('Page.getLayoutMetrics')['cssLayoutViewport']
            if layout['clientWidth']!=800 or layout['clientHeight']!=600:
                raise RuntimeError('viewport mismatch')
            yield page,cdp,d,name,origin
            browser.close()
    finally:
        if d:
            try:
                xtest.fake_input(d,X.ButtonRelease,1);d.sync();d.close()
            except Exception:
                pass
        if old is None:os.environ.pop('XAUTHORITY',None)
        else:os.environ['XAUTHORITY']=old
        auth.cleanup();proc.terminate()
        try:proc.wait(timeout=5)
        except subprocess.TimeoutExpired:proc.kill();proc.wait()


def click(d,point,origin):
    x,y=map(int,point)
    if not (0<=x<800 and 0<=y<600):raise ValueError('off-surface input')
    start=time.perf_counter_ns()
    try:
        xtest.fake_input(d,X.MotionNotify,x=x+origin[0],y=y+origin[1]);d.sync()
        xtest.fake_input(d,X.ButtonPress,1);d.sync();down=time.perf_counter_ns()
    finally:
        xtest.fake_input(d,X.ButtonRelease,1);d.sync()
    end=time.perf_counter_ns()
    empty=not d.screen().root.query_pointer().mask&(X.Button1Mask|X.Button2Mask|X.Button3Mask)
    if not empty:raise AssertionError('input release failed')
    return {'start_ns':start,'down_ack_ns':down,'up_ack_ns':end,'point':[x,y],
            'origin':list(origin),'buttons_empty':empty}


def capture(name,origin,path):
    start=time.perf_counter_ns()
    im=ImageGrab.grab(xdisplay=name).convert('RGB').crop((*origin,origin[0]+800,origin[1]+600))
    end=time.perf_counter_ns();im.save(path)
    return {'start_ns':start,'end_ns':end}
