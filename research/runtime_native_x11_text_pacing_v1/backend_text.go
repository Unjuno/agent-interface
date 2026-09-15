//go:build linux && cgo

package nativetextpacing

/*
#cgo LDFLAGS: -lX11 -ldl
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/keysym.h>
#include <dlfcn.h>
#include <stdint.h>
#include <stdlib.h>

typedef Bool (*ai_fake_key_fn)(Display*, unsigned int, Bool, unsigned long);
typedef Bool (*ai_fake_button_fn)(Display*, unsigned int, Bool, unsigned long);
typedef Bool (*ai_fake_motion_fn)(Display*, int, int, int, unsigned long);
typedef Bool (*ai_query_ext_fn)(Display*, int*, int*, int*, int*);

static void* ai_xtst_handle = NULL;
static ai_fake_key_fn ai_fk = NULL;
static ai_fake_button_fn ai_fb = NULL;
static ai_fake_motion_fn ai_fm = NULL;
static ai_query_ext_fn ai_qe = NULL;

static int ai_load_xtst(void) {
    if (ai_xtst_handle) return ai_fk && ai_fb && ai_fm && ai_qe;
    ai_xtst_handle = dlopen("libXtst.so.6", RTLD_NOW | RTLD_LOCAL);
    if (!ai_xtst_handle) return 0;
    ai_fk = (ai_fake_key_fn)dlsym(ai_xtst_handle, "XTestFakeKeyEvent");
    ai_fb = (ai_fake_button_fn)dlsym(ai_xtst_handle, "XTestFakeButtonEvent");
    ai_fm = (ai_fake_motion_fn)dlsym(ai_xtst_handle, "XTestFakeMotionEvent");
    ai_qe = (ai_query_ext_fn)dlsym(ai_xtst_handle, "XTestQueryExtension");
    return ai_fk && ai_fb && ai_fm && ai_qe;
}
static int ai_xtst_available(Display* d) {
    int a,b,c,e;
    if (!ai_load_xtst()) return 0;
    return ai_qe(d,&a,&b,&c,&e) ? 1 : 0;
}
static int ai_fake_key(Display* d, unsigned int code, int down) {
    if (!ai_fk) return 0;
    return ai_fk(d, code, down ? True : False, 0) ? 1 : 0;
}
static int ai_fake_button(Display* d, unsigned int button, int down) {
    if (!ai_fb) return 0;
    return ai_fb(d, button, down ? True : False, 0) ? 1 : 0;
}
static int ai_default_screen(Display* d) { return DefaultScreen(d); }
static int ai_fake_motion(Display* d, int screen, int x, int y) {
    if (!ai_fm) return 0;
    return ai_fm(d, screen, x, y, 0) ? 1 : 0;
}
static int ai_key_down(Display* d, unsigned int code) {
    char keys[32];
    XQueryKeymap(d, keys);
    return (keys[code >> 3] & (1 << (code & 7))) != 0;
}
static int ai_button_down(Display* d, unsigned int button) {
    Window root = DefaultRootWindow(d), rr, cr;
    int rx,ry,wx,wy; unsigned int mask=0;
    if (!XQueryPointer(d, root, &rr, &cr, &rx, &ry, &wx, &wy, &mask)) return -1;
    unsigned int bit = 0;
    switch(button) { case 1: bit=Button1Mask; break; case 2: bit=Button2Mask; break; case 3: bit=Button3Mask; break; case 4: bit=Button4Mask; break; case 5: bit=Button5Mask; break; default: return 0; }
    return (mask & bit) ? 1 : 0;
}
static unsigned long ai_keysym(const char* name) { return XStringToKeysym(name); }
static unsigned int ai_keycode(Display* d, unsigned long sym) { return XKeysymToKeycode(d, sym); }
static unsigned long ai_focus(Display* d) { Window w; int revert; XGetInputFocus(d,&w,&revert); return (unsigned long)w; }
static int ai_set_focus(Display* d, unsigned long w) { XSetInputFocus(d,(Window)w,RevertToParent,CurrentTime); XSync(d,False); return 1; }
static int ai_pointer(Display* d, int* x, int* y) {
    Window root=DefaultRootWindow(d), rr, cr; int wx,wy; unsigned int mask;
    return XQueryPointer(d, root, &rr,&cr,x,y,&wx,&wy,&mask) ? 1 : 0;
}
static int ai_window_rect(Display* d, unsigned long w, int* x, int* y, int* width, int* height) {
    XWindowAttributes a; Window child;
    if (!XGetWindowAttributes(d,(Window)w,&a)) return 0;
    int rx=0, ry=0;
    if (!XTranslateCoordinates(d,(Window)w,DefaultRootWindow(d),0,0,&rx,&ry,&child)) return 0;
    *x=rx; *y=ry; *width=a.width; *height=a.height; return 1;
}
static uint64_t ai_capture_hash(Display* d, unsigned long w, int* ok) {
    XWindowAttributes a;
    if (!XGetWindowAttributes(d,(Window)w,&a) || a.width<=0 || a.height<=0) { *ok=0; return 0; }
    XImage* img=XGetImage(d,(Window)w,0,0,(unsigned int)a.width,(unsigned int)a.height,AllPlanes,ZPixmap);
    if (!img) { *ok=0; return 0; }
    uint64_t h=1469598103934665603ULL;
    for (int y=0;y<a.height;y++) for(int x=0;x<a.width;x++) {
        unsigned long p=XGetPixel(img,x,y);
        for(int i=0;i<sizeof(unsigned long);i++){ h ^= (uint8_t)(p>>(i*8)); h *= 1099511628211ULL; }
    }
    XDestroyImage(img); *ok=1; return h;
}
*/
import "C"

import (
	core "agentinterface/nativecore"
	"fmt"
	"strconv"
	"strings"
	"time"
	"unsafe"
)

type Backend struct {
	d           *C.Display
	started     time.Time
	targets     map[string]C.ulong
	focused     C.ulong
	heldKeys    map[C.uint]bool
	heldButtons map[C.uint]bool
	xtest       bool
	injected    int
	textPacing  time.Duration
}

type Receipt struct {
	Accepted                 bool    `json:"accepted"`
	Error                    string  `json:"error,omitempty"`
	InjectedEvents           int     `json:"injected_events"`
	FocusVerified            bool    `json:"focus_verified"`
	KeyDownObserved          bool    `json:"key_down_observed"`
	PointerVerified          bool    `json:"pointer_verified"`
	CaptureBefore            uint64  `json:"capture_before"`
	CaptureBeforeOK          bool    `json:"capture_before_ok"`
	CaptureBeforeRelease     uint64  `json:"capture_before_release"`
	CaptureBeforeReleaseOK   bool    `json:"capture_before_release_ok"`
	CaptureChanged           bool    `json:"capture_changed"`
	FinalReleaseVerified     bool    `json:"final_release_verified"`
	TextCharacters           int     `json:"text_characters"`
	TextCharDurationsNS      []int64 `json:"text_char_durations_ns,omitempty"`
	TextCharStartIntervalsNS []int64 `json:"text_char_start_intervals_ns,omitempty"`
}

func Open(display string, textPacing time.Duration) (*Backend, error) {
	if textPacing < 0 || textPacing > 100*time.Millisecond {
		return nil, fmt.Errorf("text pacing out of range")
	}
	var c *C.char
	if display != "" {
		c = C.CString(display)
		defer C.free(unsafe.Pointer(c))
	}
	d := C.XOpenDisplay(c)
	if d == nil {
		return nil, fmt.Errorf("XOpenDisplay failed")
	}
	b := &Backend{d: d, started: time.Now(), targets: map[string]C.ulong{}, heldKeys: map[C.uint]bool{}, heldButtons: map[C.uint]bool{}, textPacing: textPacing}
	b.xtest = C.ai_xtst_available(d) != 0
	return b, nil
}
func (b *Backend) Close() {
	if b.d != nil {
		b.releaseAll()
		C.XCloseDisplay(b.d)
		b.d = nil
	}
}
func (b *Backend) NowNS() int64                           { return time.Since(b.started).Nanoseconds() }
func (b *Backend) RegisterTarget(name string, xid uint64) { b.targets[name] = C.ulong(xid) }
func (b *Backend) Manifest() core.Manifest {
	var m core.Manifest
	m.Schema = core.SchemaBackend
	m.BackendID = "native-x11-text-v1"
	m.Platform.OS = "linux"
	m.Platform.Backend = "x11"
	m.Capabilities = map[string]core.Capability{}
	for c := range core.KnownCapabilities {
		m.Capabilities[c] = core.Capability{State: "unsupported"}
	}
	for _, c := range []string{"capture.frame", "window.focus", "display.geometry", "clock.monotonic"} {
		m.Capabilities[c] = core.Capability{State: "supported"}
	}
	if b.xtest {
		for _, c := range []string{"input.keyboard", "input.text", "input.pointer", "input.release_all"} {
			m.Capabilities[c] = core.Capability{State: "supported"}
		}
	}
	m.CoordinateFrames = []string{"screen_physical_px", "window_client"}
	m.Clock.Unit = "ns"
	m.Clock.Monotonic = true
	return m
}
func keysymName(k string) string {
	switch k {
	case "CTRL":
		return "Control_L"
	case "SHIFT":
		return "Shift_L"
	case "ALT":
		return "Alt_L"
	case "ENTER":
		return "Return"
	case "ESC":
		return "Escape"
	}
	return k
}
func (b *Backend) keycode(k string) (C.uint, error) {
	cs := C.CString(keysymName(k))
	defer C.free(unsafe.Pointer(cs))
	sym := C.ai_keysym(cs)
	if sym == 0 {
		return 0, fmt.Errorf("unknown key %s", k)
	}
	code := C.ai_keycode(b.d, sym)
	if code == 0 {
		return 0, fmt.Errorf("no keycode %s", k)
	}
	return code, nil
}
func (b *Backend) fakeKey(code C.uint, down bool) error {
	v := 0
	if down {
		v = 1
	}
	if C.ai_fake_key(b.d, code, C.int(v)) == 0 {
		return fmt.Errorf("XTestFakeKeyEvent failed")
	}
	C.XSync(b.d, C.False)
	b.injected++
	if down {
		b.heldKeys[code] = true
	} else {
		delete(b.heldKeys, code)
	}
	return nil
}
func (b *Backend) fakeButton(btn C.uint, down bool) error {
	v := 0
	if down {
		v = 1
	}
	if C.ai_fake_button(b.d, btn, C.int(v)) == 0 {
		return fmt.Errorf("XTestFakeButtonEvent failed")
	}
	C.XSync(b.d, C.False)
	b.injected++
	if down {
		b.heldButtons[btn] = true
	} else {
		delete(b.heldButtons, btn)
	}
	return nil
}
func buttonNum(s string) (C.uint, error) {
	switch s {
	case "left":
		return 1, nil
	case "middle":
		return 2, nil
	case "right":
		return 3, nil
	}
	return 0, fmt.Errorf("unsupported button %s", s)
}
func (b *Backend) capture(w C.ulong) (uint64, bool) {
	var ok C.int
	h := C.ai_capture_hash(b.d, w, &ok)
	return uint64(h), ok != 0
}
func (b *Backend) releaseAll() bool {
	ok := true
	keys := make([]C.uint, 0, len(b.heldKeys))
	for code := range b.heldKeys {
		keys = append(keys, code)
	}
	buttons := make([]C.uint, 0, len(b.heldButtons))
	for btn := range b.heldButtons {
		buttons = append(buttons, btn)
	}
	for _, code := range keys {
		if err := b.fakeKey(code, false); err != nil {
			ok = false
		}
	}
	for _, btn := range buttons {
		if err := b.fakeButton(btn, false); err != nil {
			ok = false
		}
	}
	C.XSync(b.d, C.False)
	for _, code := range keys {
		if C.ai_key_down(b.d, code) != 0 {
			ok = false
		}
	}
	for _, btn := range buttons {
		if C.ai_button_down(b.d, btn) != 0 {
			ok = false
		}
	}
	return ok && len(b.heldKeys) == 0 && len(b.heldButtons) == 0
}
func textSubsetOK(p core.Program) bool {
	for _, op := range p.Ops {
		if op.Op != "text" {
			continue
		}
		for _, r := range op.Text {
			if r < 'a' || r > 'z' {
				return false
			}
		}
	}
	return true
}
func (b *Backend) Execute(p core.Program, currentSeq, currentRev int64) Receipt {
	startInjected := b.injected
	if !textSubsetOK(p) {
		return Receipt{Accepted: false, Error: "TEXT_SUBSET_UNSUPPORTED"}
	}
	adm := core.Admit(p, b.Manifest(), b.NowNS(), currentSeq, currentRev)
	r := Receipt{Accepted: adm.Accepted, Error: adm.Error}
	if !adm.Accepted {
		return r
	}
	if b.focused != 0 {
		r.CaptureBefore, r.CaptureBeforeOK = b.capture(b.focused)
	}
	for _, op := range p.Ops {
		switch op.Op {
		case "focus":
			w, ok := b.targets[op.Target]
			if !ok {
				r.Error = "UNKNOWN_TARGET"
				r.FinalReleaseVerified = b.releaseAll()
				r.InjectedEvents = b.injected - startInjected
				return r
			}
			C.ai_set_focus(b.d, C.ulong(w))
			b.focused = w
			r.FocusVerified = C.ai_focus(b.d) == C.ulong(w)
			if !r.CaptureBeforeOK {
				r.CaptureBefore, r.CaptureBeforeOK = b.capture(w)
			}
		case "key_state":
			code, e := b.keycode(op.Key)
			if e != nil {
				r.Error = e.Error()
				break
			}
			if e = b.fakeKey(code, *op.Down); e != nil {
				r.Error = e.Error()
				break
			}
			if *op.Down {
				r.KeyDownObserved = C.ai_key_down(b.d, code) != 0
			}
		case "key_chord":
			codes := []C.uint{}
			for _, k := range op.Keys {
				code, e := b.keycode(k)
				if e != nil {
					r.Error = e.Error()
					break
				}
				codes = append(codes, code)
				if e = b.fakeKey(code, true); e != nil {
					r.Error = e.Error()
					break
				}
			}
			for i := len(codes) - 1; i >= 0; i-- {
				_ = b.fakeKey(codes[i], false)
			}
		case "text":
			var prevStart time.Time
			for _, ch := range op.Text {
				started := time.Now()
				if !prevStart.IsZero() {
					r.TextCharStartIntervalsNS = append(r.TextCharStartIntervalsNS, started.Sub(prevStart).Nanoseconds())
				}
				prevStart = started
				code, e := b.keycode(string(ch))
				if e != nil {
					r.Error = e.Error()
					break
				}
				if e = b.fakeKey(code, true); e != nil {
					r.Error = e.Error()
					break
				}
				if e = b.fakeKey(code, false); e != nil {
					r.Error = e.Error()
					break
				}
				r.TextCharacters++
				r.TextCharDurationsNS = append(r.TextCharDurationsNS, time.Since(started).Nanoseconds())
				if b.textPacing > 0 {
					time.Sleep(b.textPacing)
				}
			}
		case "pointer_move":
			x, y := op.X, op.Y
			if op.Frame == "window_client" {
				var rx, ry, w, h C.int
				if C.ai_window_rect(b.d, C.ulong(b.focused), &rx, &ry, &w, &h) == 0 {
					r.Error = "WINDOW_GEOMETRY"
					break
				}
				x += int(rx)
				y += int(ry)
			}
			if C.ai_fake_motion(b.d, C.int(C.ai_default_screen(b.d)), C.int(x), C.int(y)) == 0 {
				r.Error = "POINTER_MOVE"
				break
			}
			C.XSync(b.d, C.False)
			b.injected++
			var qx, qy C.int
			if C.ai_pointer(b.d, &qx, &qy) != 0 {
				r.PointerVerified = int(qx) == x && int(qy) == y
			}
		case "pointer_button":
			btn, e := buttonNum(op.Button)
			if e != nil {
				r.Error = e.Error()
				break
			}
			if e = b.fakeButton(btn, *op.Down); e != nil {
				r.Error = e.Error()
				break
			}
		case "scroll":
			btn := C.uint(5)
			n := op.DY
			if n < 0 {
				btn = 4
				n = -n
			}
			if n > 20 {
				n = 20
			}
			for i := 0; i < n; i++ {
				if e := b.fakeButton(btn, true); e != nil {
					r.Error = e.Error()
					break
				}
				_ = b.fakeButton(btn, false)
			}
		case "release_all":
			if b.focused != 0 {
				r.CaptureBeforeRelease, r.CaptureBeforeReleaseOK = b.capture(b.focused)
				r.CaptureChanged = r.CaptureBeforeOK && r.CaptureBeforeReleaseOK && r.CaptureBefore != r.CaptureBeforeRelease
			}
			r.FinalReleaseVerified = b.releaseAll()
		default:
			r.Error = "UNIMPLEMENTED_OP_" + strings.ToUpper(op.Op)
		}
		if r.Error != "" {
			break
		}
	}
	if r.Error != "" && !r.FinalReleaseVerified {
		r.FinalReleaseVerified = b.releaseAll()
	}
	r.InjectedEvents = b.injected - startInjected
	return r
}

func ParseXID(s string) (uint64, error) { return strconv.ParseUint(strings.TrimSpace(s), 0, 64) }
