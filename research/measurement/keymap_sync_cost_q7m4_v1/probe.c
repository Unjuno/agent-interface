/* Research-only private-Xvfb observation microbenchmark; no task dispatch. */
#define _POSIX_C_SOURCE 200809L
#include <X11/Xlib.h>
#include <X11/XKBlib.h>
#include <X11/keysym.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
typedef int (*Fake)(Display*,unsigned int,Bool,unsigned long);
typedef struct { int known,down,focus,pending; } State;
typedef struct { int type,code,mode,detail,synthetic; unsigned long window; char map[65]; } Event;
static unsigned long long tick(clockid_t id){struct timespec t;if(clock_gettime(id,&t))exit(90);return (unsigned long long)t.tv_sec*1000000000ULL+t.tv_nsec;}
static void hexmap(const char*m,char*s){for(int i=0;i<32;i++)sprintf(s+2*i,"%02x",(unsigned char)m[i]);s[64]=0;}
static int bit(const char*m,int code){return !!((unsigned char)m[code/8]&(1U<<(code%8)));}
static int drain(Display*d,Window w,int code,State*s,Event*out){
 int n=0;
 while(XEventsQueued(d,QueuedAlready)){
  XEvent x;XNextEvent(d,&x);
  if(x.type!=KeyPress&&x.type!=KeyRelease&&x.type!=FocusIn&&x.type!=FocusOut&&x.type!=KeymapNotify)continue;
  if(n>=64)exit(91);
  Event*e=&out[n++];memset(e,0,sizeof(*e));e->type=x.type;e->synthetic=x.xany.send_event;
  if(e->synthetic){s->known=0;continue;}
  if(x.type==KeymapNotify){hexmap(x.xkeymap.key_vector,e->map);if(s->pending&&s->focus){s->down=bit(x.xkeymap.key_vector,code);s->known=1;}else s->known=0;s->pending=0;}
  else if(x.type==FocusIn||x.type==FocusOut){e->window=x.xfocus.window;e->mode=x.xfocus.mode;e->detail=x.xfocus.detail;s->known=0;s->focus=x.type==FocusIn&&x.xfocus.mode==NotifyNormal&&x.xfocus.window==w;s->pending=s->focus;}
  else {e->window=x.xkey.window;e->code=x.xkey.keycode;if(s->pending){s->known=0;s->pending=0;}if(e->window!=w)s->known=0;else if(e->code==code)s->down=x.type==KeyPress;}
 }
 return n;
}
static void events(Event*e,int n){putchar('[');for(int i=0;i<n;i++)printf("%s{\"type\":%d,\"code\":%d,\"mode\":%d,\"detail\":%d,\"synthetic\":%d,\"window\":%lu,\"map\":\"%s\"}",i?",":"",e[i].type,e[i].code,e[i].mode,e[i].detail,e[i].synthetic,e[i].window,e[i].map);putchar(']');}
int main(int argc,char**argv){
 if(argc!=6||argv[1][0]!=':')return 64;
 int arm=atoi(argv[2]),scenario=atoi(argv[3]),samples=atoi(argv[4]),warmup=atoi(argv[5]);
 if(arm<0||arm>2||scenario<0||scenario>3||samples<1||samples>64||warmup!=2)return 64;
 setvbuf(stdout,NULL,_IOLBF,0);
 void*lib=dlopen("libXtst.so.6",RTLD_NOW);if(!lib)return 65;
 Fake fake=(Fake)dlsym(lib,"XTestFakeKeyEvent");if(!fake)return 65;
 Display*a=XOpenDisplay(argv[1]),*d=XOpenDisplay(argv[1]),*o=XOpenDisplay(argv[1]);if(!a||!d||!o)return 66;
 unsigned int code=XKeysymToKeycode(a,XK_Shift_L);if(code<8)return 67;
 Window root=DefaultRootWindow(a),w=XCreateSimpleWindow(a,root,10,10,100,80,0,0,0),away=XCreateSimpleWindow(a,root,150,10,100,80,0,0,0);
 XMapWindow(a,w);XMapWindow(a,away);XAutoRepeatOff(a);XSync(a,False);
 Bool supported=False;if(!XkbSetDetectableAutoRepeat(d,True,&supported)||!supported)return 68;
 XSelectInput(d,w,KeyPressMask|KeyReleaseMask|FocusChangeMask|KeymapStateMask);XSync(d,False);
 printf("{\"kind\":\"start\",\"pid\":%ld,\"arm\":%d,\"scenario\":%d,\"samples\":%d,\"warmup\":%d,\"window\":%lu,\"away\":%lu,\"code\":%u,\"vendor\":\"%s\",\"release\":%d}\n",(long)getpid(),arm,scenario,samples,warmup,w,away,code,ServerVendor(d),VendorRelease(d));
 for(int i=-warmup;i<samples;i++){
  /* Identical quiescent seed; all setup and oracle queries are outside timing. */
  fake(a,code,False,0);XSetInputFocus(a,away,RevertToParent,CurrentTime);XSync(a,False);
  XSync(d,False);while(XEventsQueued(d,QueuedAlready)){XEvent x;XNextEvent(d,&x);}
  XSetInputFocus(a,w,RevertToParent,CurrentTime);XSync(a,False);XSync(d,False);
  State s={0,0,0,0};Event bootstrap[64],ev[64];int nb=drain(d,w,code,&s,bootstrap);if(!s.known||s.down||!s.focus)return 69;
  if(scenario==1)fake(a,code,True,0);
  if(scenario>=2){XSetInputFocus(a,away,RevertToParent,CurrentTime);fake(a,code,True,0);XSetInputFocus(a,w,RevertToParent,CurrentTime);if(scenario==3)fake(a,code,False,0);}
  XSync(a,False);
  char pre[32],post[32],q[32]={0},ph[65],qh[65],ah[65];
  unsigned long long ob=tick(CLOCK_MONOTONIC);XQueryKeymap(o,pre);unsigned long long oe=tick(CLOCK_MONOTONIC);
  unsigned long rb=XNextRequest(d);unsigned long long t0=tick(CLOCK_MONOTONIC),c0=tick(CLOCK_PROCESS_CPUTIME_ID);
  if(arm!=1)XSync(d,False);
  if(arm!=0)XQueryKeymap(d,q);
  int ne=drain(d,w,code,&s,ev);int decision=arm==0?(s.known&&s.focus?s.down:-1):bit(q,code);
  unsigned long long c1=tick(CLOCK_PROCESS_CPUTIME_ID),t1=tick(CLOCK_MONOTONIC);unsigned long ra=XNextRequest(d),processed=XLastKnownRequestProcessed(d);
  unsigned long long pb=tick(CLOCK_MONOTONIC);XQueryKeymap(o,post);unsigned long long pe=tick(CLOCK_MONOTONIC);
  hexmap(pre,ph);hexmap(q,qh);hexmap(post,ah);
  printf("{\"kind\":\"sample\",\"index\":%d,\"before_ns\":%llu,\"after_ns\":%llu,\"cpu_before_ns\":%llu,\"cpu_after_ns\":%llu,\"request_before\":%lu,\"request_after\":%lu,\"processed\":%lu,\"oracle_before_begin\":%llu,\"oracle_before_end\":%llu,\"oracle_after_begin\":%llu,\"oracle_after_end\":%llu,\"pre\":\"%s\",\"post\":\"%s\",\"query\":\"%s\",\"known\":%d,\"down\":%d,\"focus\":%d,\"decision\":%d,\"bootstrap\":",i,t0,t1,c0,c1,rb,ra,processed,ob,oe,pb,pe,ph,ah,qh,s.known,s.down,s.focus,decision);events(bootstrap,nb);printf(",\"events\":");events(ev,ne);puts("}");
 }
 fake(a,code,False,0);XSync(a,False);char final[32],fh[65];XQueryKeymap(o,final);hexmap(final,fh);
 Window rr,cr;int rx,ry,wx,wy;unsigned int mask;XQueryPointer(o,root,&rr,&cr,&rx,&ry,&wx,&wy,&mask);
 printf("{\"kind\":\"end\",\"final_keymap\":\"%s\",\"pointer_mask\":%u}\n",fh,mask);
 XDestroyWindow(a,w);XDestroyWindow(a,away);XCloseDisplay(o);XCloseDisplay(d);XCloseDisplay(a);dlclose(lib);return 0;
}
