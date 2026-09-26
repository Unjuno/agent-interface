/* Scoped, read-only X11 acquisition instrumentation. No task input methods.
 * EVENT_SYNC preserves the predecessor's XSync(False)/XPending/XNextEvent path.
 * The caller supplies only its private target, never expected states or cases.
 */
#define _POSIX_C_SOURCE 200809L
#include <X11/Xlib.h>
#include <X11/XKBlib.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#define CAP 96
typedef struct { uint64_t ordinal,window,server_ms,dequeued_ns;
 int type,send_event,keycode,mode,detail; unsigned char keymap[32]; } Event;
typedef struct { uint64_t t0,t1,r0,r1,p0,p1; int count,queries,syncs,errors;
 unsigned char keymap[32]; Event events[CAP]; } Sample;
typedef struct { Display *d; Window window; uint64_t ordinal; int subscribed; } Ctx;
static int error_count=0;
static int on_error(Display*d,XErrorEvent*e){(void)d;(void)e;error_count++;return 0;}
static uint64_t ns(void){struct timespec t; if(clock_gettime(CLOCK_MONOTONIC,&t))abort();return (uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec;}
size_t ks_sample_size(void){return sizeof(Sample);}
size_t ks_event_size(void){return sizeof(Event);}
void *ks_open(unsigned long w,int subscribed){
 Ctx *c=calloc(1,sizeof *c); if(!c)return NULL;
 XSetErrorHandler(on_error); c->d=XOpenDisplay(NULL); if(!c->d){free(c);return NULL;}
 c->window=w;c->subscribed=subscribed; Bool supported=False,active=False;
 if(!XkbSetDetectableAutoRepeat(c->d,True,&supported)||!XkbGetDetectableAutoRepeat(c->d,&active)||!supported||!active){XCloseDisplay(c->d);free(c);return NULL;}
 long mask=subscribed?(KeyPressMask|KeyReleaseMask|FocusChangeMask|KeymapStateMask):0;
 XSelectInput(c->d,w,mask);XSync(c->d,False);
 XWindowAttributes a;if(!XGetWindowAttributes(c->d,w,&a)||a.your_event_mask!=mask||error_count){XCloseDisplay(c->d);free(c);return NULL;}
 return c;
}
int ks_observe(void *opaque,int mode,Sample*s){
 Ctx*c=opaque;if(!c||!s||mode<0||mode>2)return -1;
 if(mode!=0&&!c->subscribed)return -2;
 memset(s,0,sizeof *s);s->r0=XNextRequest(c->d);s->p0=XLastKnownRequestProcessed(c->d);s->t0=ns();
 if(mode==0){s->queries=1;if(!XQueryKeymap(c->d,(char*)s->keymap))return -3;}
 else{
  if(mode==1){s->syncs=1;XSync(c->d,False);}
  while(mode==2?XEventsQueued(c->d,QueuedAlready):XPending(c->d)){
   XEvent e;memset(&e,0,sizeof e);XNextEvent(c->d,&e);
   if(e.type!=KeyPress&&e.type!=KeyRelease&&e.type!=FocusIn&&e.type!=FocusOut&&e.type!=KeymapNotify)continue;
   if(s->count>=CAP)return -4;
   Event*v=&s->events[s->count++];v->ordinal=c->ordinal++;v->type=e.type;v->send_event=e.xany.send_event;v->dequeued_ns=ns();
   if(e.type==KeymapNotify)memcpy(v->keymap,e.xkeymap.key_vector,32);
   else if(e.type==FocusIn||e.type==FocusOut){v->window=e.xfocus.window;v->mode=e.xfocus.mode;v->detail=e.xfocus.detail;}
   else {v->window=e.xkey.window;v->keycode=e.xkey.keycode;v->server_ms=e.xkey.time;}
  }
 }
 s->t1=ns();s->r1=XNextRequest(c->d);s->p1=XLastKnownRequestProcessed(c->d);s->errors=error_count;return error_count?-5:0;
}
int ks_close(void*opaque){Ctx*c=opaque;if(!c)return -1;XCloseDisplay(c->d);free(c);return error_count?-1:0;}

/* New read-only composition endpoint. Same Ctx and same Xlib connection. */
typedef struct {uint64_t t0,t1,r0,r1,p0,p1,focus; int revert,errors;} FocusSample;
size_t ks_focus_size(void){return sizeof(FocusSample);}
int ks_focus(void *opaque,FocusSample *s){
 Ctx*c=opaque;if(!c||!s)return -1;memset(s,0,sizeof *s);
 Window focus;int revert;s->r0=XNextRequest(c->d);s->p0=XLastKnownRequestProcessed(c->d);s->t0=ns();
 int ok=XGetInputFocus(c->d,&focus,&revert);
 s->t1=ns();s->r1=XNextRequest(c->d);s->p1=XLastKnownRequestProcessed(c->d);
 s->focus=focus;s->revert=revert;s->errors=error_count;
 return ok&&!error_count?0:-2;
}
