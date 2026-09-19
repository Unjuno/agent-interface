package main

/*
#cgo LDFLAGS: -lX11
#include <X11/Xlib.h>
#include <stdlib.h>
static unsigned long mk(Display*d){int s=DefaultScreen(d); Window root=RootWindow(d,s); Window w=XCreateSimpleWindow(d,root,100,100,320,200,1,BlackPixel(d,s),WhitePixel(d,s)); XStoreName(d,w,"AgentInterfaceNativeX11Fixture"); XSelectInput(d,w,ExposureMask|KeyPressMask|KeyReleaseMask|ButtonPressMask|ButtonReleaseMask); XMapWindow(d,w); XFlush(d); return (unsigned long)w;}
static int next(Display*d,XEvent*e){XNextEvent(d,e);return e->type;}
static unsigned int keycode(XEvent*e){return e->xkey.keycode;}
static unsigned int button(XEvent*e){return e->xbutton.button;}
static void color(Display*d,unsigned long w,unsigned long c){XSetWindowBackground(d,(Window)w,c);XClearWindow(d,(Window)w);XFlush(d);}
*/
import "C"
import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"time"
)

func main() {
	ready := flag.String("ready", "", "ready")
	ledger := flag.String("ledger", "", "ledger")
	flag.Parse()
	if *ready == "" || *ledger == "" {
		panic("paths required")
	}
	d := C.XOpenDisplay(nil)
	if d == nil {
		panic("display")
	}
	defer C.XCloseDisplay(d)
	w := C.mk(d)
	os.WriteFile(*ready, []byte(fmt.Sprintf("0x%x\n", uint64(w))), 0644)
	f, e := os.Create(*ledger)
	if e != nil {
		panic(e)
	}
	defer f.Close()
	counts := map[string]int{}
	enc := json.NewEncoder(f)
	for {
		var ev C.XEvent
		t := int(C.next(d, &ev))
		name := ""
		detail := uint(0)
		switch t {
		case C.KeyPress:
			name = "key_press"
			detail = uint(C.keycode(&ev))
			C.color(d, w, 0x2060ff)
		case C.KeyRelease:
			name = "key_release"
			detail = uint(C.keycode(&ev))
		case C.ButtonPress:
			name = "button_press"
			detail = uint(C.button(&ev))
			C.color(d, w, 0xff6020)
		case C.ButtonRelease:
			name = "button_release"
			detail = uint(C.button(&ev))
		case C.Expose:
			continue
		default:
			continue
		}
		counts[name]++
		enc.Encode(map[string]any{"event": name, "detail": detail, "unix_ns": time.Now().UnixNano()})
		f.Sync()
		if counts["key_press"] >= 1 && counts["key_release"] >= 1 && counts["button_press"] >= 1 && counts["button_release"] >= 1 {
			return
		}
	}
}
