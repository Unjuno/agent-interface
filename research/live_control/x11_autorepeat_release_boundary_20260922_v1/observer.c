/* Research fixture: observes ONLY the caller-owned window passed on argv.
 * No root/global keyboard event selection; DISPLAY must name a private Xvfb.
 */
#define _POSIX_C_SOURCE 200809L
#include <X11/Xlib.h>
#include <X11/XKBlib.h>
#include <X11/keysym.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <errno.h>

static unsigned long long ns(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) { perror("clock_gettime"); exit(91); }
    return (unsigned long long)t.tv_sec * 1000000000ULL + t.tv_nsec;
}
static void maphex(const char map[32], char out[65]) {
    for (int i=0;i<32;i++) sprintf(out+2*i,"%02x",(unsigned char)map[i]);
    out[64]=0;
}
static void sample(Display *d, const char *kind, const char *id, int code) {
    char map[32], hex[65]; unsigned long long a=ns(); XQueryKeymap(d,map);
    unsigned long long b=ns(); maphex(map,hex);
    printf("{\"kind\":\"%s\",\"id\":\"%s\",\"pid\":%ld,\"before_ns\":%llu,\"after_ns\":%llu,\"keymap\":\"%s\",\"keycode\":%d,\"down\":%s}\n",kind,id,(long)getpid(),a,b,hex,code,((unsigned char)map[code/8]&(1u<<(code%8)))?"true":"false");
}
int main(int argc,char **argv) {
    setvbuf(stdout,NULL,_IOLBF,0);
    if(argc<2) return 64;
    Display *d=XOpenDisplay(NULL); if(!d){fprintf(stderr,"private display unavailable\n");return 65;}
    if(!strcmp(argv[1],"config")) {
        if(argc!=5) return 64;
        int enabled=atoi(argv[2]); unsigned delay=(unsigned)atoi(argv[3]), interval=(unsigned)atoi(argv[4]);
        int op,ev,err,maj=XkbMajorVersion,min=XkbMinorVersion;
        Bool ext=XkbQueryExtension(d,&op,&ev,&err,&maj,&min);
        if(!ext) return 66;
        if(!XkbSetAutoRepeatRate(d,XkbUseCoreKbd,delay,interval)) return 67;
        XKeyboardControl ctl; memset(&ctl,0,sizeof(ctl)); ctl.key=XKeysymToKeycode(d,XK_a);ctl.auto_repeat_mode=AutoRepeatModeOn;
        XChangeKeyboardControl(d,KBKey|KBAutoRepeatMode,&ctl);
        if(enabled) XAutoRepeatOn(d); else XAutoRepeatOff(d); XSync(d,False);
        unsigned got_delay=0,got_interval=0;Bool got=XkbGetAutoRepeatRate(d,XkbUseCoreKbd,&got_delay,&got_interval);
        XKeyboardState k; XGetKeyboardControl(d,&k); char hex[65];maphex(k.auto_repeats,hex);
        printf("{\"kind\":\"config\",\"pid\":%ld,\"xkb\":%s,\"get_rate\":%s,\"delay_ms\":%u,\"interval_ms\":%u,\"global_repeat\":%d,\"per_key_repeat\":\"%s\",\"keycode\":%u}\n",(long)getpid(),ext?"true":"false",got?"true":"false",got_delay,got_interval,k.global_auto_repeat,hex,ctl.key);
        XCloseDisplay(d); return got?0:68;
    }
    if(strcmp(argv[1],"observe")||argc!=4) return 64;
    char *end=NULL;unsigned long w=strtoul(argv[2],&end,10);if(!w||*end)return 64;
    int wanted=atoi(argv[3]);if(wanted!=0&&wanted!=1)return 64;
    Bool supported=False,got_supported=False;
    Bool result=XkbSetDetectableAutoRepeat(d,wanted,&supported);
    Bool actual=XkbGetDetectableAutoRepeat(d,&got_supported);
    XSelectInput(d,(Window)w,KeyPressMask|KeyReleaseMask);XSync(d,False);
    int code=XKeysymToKeycode(d,XK_a); XWindowAttributes at;XGetWindowAttributes(d,w,&at);
    printf("{\"kind\":\"ready\",\"pid\":%ld,\"window\":%lu,\"keycode\":%d,\"requested_detectable\":%s,\"setter_state\":%s,\"detectable\":%s,\"supported\":%s,\"get_supported\":%s,\"event_mask\":%ld,\"ns\":%llu}\n",(long)getpid(),w,code,wanted?"true":"false",result?"true":"false",actual?"true":"false",supported?"true":"false",got_supported?"true":"false",at.your_event_mask,ns());
    unsigned delay=0,interval=0; Bool gr=XkbGetAutoRepeatRate(d,XkbUseCoreKbd,&delay,&interval); XKeyboardState k;XGetKeyboardControl(d,&k);
    printf("{\"kind\":\"rate\",\"get_rate\":%s,\"delay_ms\":%u,\"interval_ms\":%u,\"global_repeat\":%d}\n",gr?"true":"false",delay,interval,k.global_auto_repeat);
    char buf[4096];size_t used=0;unsigned n=0;int running=1;
    while(running) {
        while(XPending(d)) {
            XEvent e;XNextEvent(d,&e);
            if(e.type!=KeyPress&&e.type!=KeyRelease) continue;
            char map[32],hex[65];unsigned long long a=ns();XQueryKeymap(d,map);unsigned long long b=ns();maphex(map,hex);
            unsigned kc=e.xkey.keycode;
            printf("{\"kind\":\"event\",\"index\":%u,\"pid\":%ld,\"type\":%d,\"window\":%lu,\"keycode\":%u,\"server_time_ms\":%lu,\"state\":%u,\"send_event\":%s,\"serial\":%lu,\"before_ns\":%llu,\"after_ns\":%llu,\"keymap\":\"%s\",\"down\":%s}\n",n++,(long)getpid(),e.type,e.xkey.window,kc,e.xkey.time,e.xkey.state,e.xkey.send_event?"true":"false",e.xkey.serial,a,b,hex,((unsigned char)map[kc/8]&(1u<<(kc%8)))?"true":"false");
        }
        struct pollfd p[2]={{ConnectionNumber(d),POLLIN,0},{STDIN_FILENO,POLLIN|POLLHUP,0}};
        int r=poll(p,2,1000);if(r<0){if(errno==EINTR)continue;perror("poll");return 69;}
        if(p[1].revents&(POLLIN|POLLHUP)) {
            ssize_t nread=read(0,buf+used,sizeof(buf)-used-1);if(nread<=0)break;used+=(size_t)nread;buf[used]=0;
            char *line=buf,*nl;
            while((nl=strchr(line,'\n'))) {
                *nl=0;
                if(!strcmp(line,"STOP")){sample(d,"terminal","stop",code);running=0;}
                else if(!strncmp(line,"SNAP ",5)){
                    const char *id=line+5;if(strspn(id,"abcdefghijklmnopqrstuvwxyz0123456789_-")!=strlen(id))return 70;
                    sample(d,"sample",id,code);
                } else return 71;
                line=nl+1;
            }
            size_t rest=used-(size_t)(line-buf);memmove(buf,line,rest);used=rest;
            if(used>=sizeof(buf)-1)return 72;
        }
    }
    XCloseDisplay(d);return 0;
}
