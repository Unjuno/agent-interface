#define _POSIX_C_SOURCE 200809L
#include "facility.h"

#include <X11/Xlib.h>
#include <X11/keysym.h>
#include <X11/Xutil.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static double now_sec(void){ struct timespec ts; clock_gettime(CLOCK_MONOTONIC,&ts); return ts.tv_sec+ts.tv_nsec/1e9; }
static void sleep_frame(void){ struct timespec ts={0,16667000}; nanosleep(&ts,NULL); }

static void usage(const char *argv0){
    fprintf(stderr,"usage: %s [--seed N] [--difficulty D] [--set k=v] [--headless|--gui] [--auto-reference] [--report FILE] [--snapshot FILE] [--benchmark N] [--render-benchmark N] [--no-sleep]\n",argv0);
}

static int parse_set(Difficulty *d,const char *s){ const char *eq=strchr(s,'='); if(!eq)return-1; char key[96]; size_t n=(size_t)(eq-s); if(n==0||n>=sizeof(key))return-1; memcpy(key,s,n);key[n]='\0'; char *end=NULL; double v=strtod(eq+1,&end); if(!end||*end)return-1; return difficulty_set(d,key,v); }

static int run_episode(uint64_t seed,Difficulty d,int render_each,int snapshot,const char *snapshot_path,Facility *out){
    Facility f; facility_init(&f,seed,d); ReferenceController r; reference_init(&r); FacilityInput in; uint32_t *pix=render_each||snapshot?calloc(FACILITY_W*FACILITY_H,sizeof(uint32_t)):NULL; int guard=d.episode_deadline_ticks+10;
    while(!f.done && guard--){ reference_next(&f,&r,&in); facility_step(&f,&in); if(render_each)facility_render(&f,pix,FACILITY_W,FACILITY_H); }
    if(snapshot){ facility_render(&f,pix,FACILITY_W,FACILITY_H); if(snapshot_path)facility_write_ppm(pix,FACILITY_W,FACILITY_H,snapshot_path); }
    if(out) *out=f;
    free(pix);
    return f.success?0:1;
}

static int run_gui(uint64_t seed,Difficulty d,int auto_ref,int no_sleep,const char *report_path){
    Display *disp=XOpenDisplay(NULL); if(!disp){fprintf(stderr,"XOpenDisplay failed\n");return 2;} int screen=DefaultScreen(disp); Window root=RootWindow(disp,screen); Window win=XCreateSimpleWindow(disp,root,0,0,FACILITY_W,FACILITY_H,0,BlackPixel(disp,screen),BlackPixel(disp,screen)); XStoreName(disp,win,"Procedural Operations Facility v0"); XSelectInput(disp,win,ExposureMask|KeyPressMask|KeyReleaseMask|ButtonPressMask|ButtonReleaseMask|PointerMotionMask|StructureNotifyMask); XMapWindow(disp,win); GC gc=XCreateGC(disp,win,0,NULL);
    uint32_t *pix=calloc(FACILITY_W*FACILITY_H,sizeof(uint32_t)); XImage *img=XCreateImage(disp,DefaultVisual(disp,screen),DefaultDepth(disp,screen),ZPixmap,0,(char*)pix,FACILITY_W,FACILITY_H,32,0); if(!img){fprintf(stderr,"XCreateImage failed\n");return 2;}
    Facility f; facility_init(&f,seed,d); ReferenceController ref; reference_init(&ref); FacilityInput next; facility_input_clear(&next); int key_w=0,key_s=0,key_a=0,key_d=0; int mouse_down=0; double start=now_sec(); int closed=0;
    while(!closed && !f.done){
        while(XPending(disp)){
            XEvent e; XNextEvent(disp,&e);
            if(e.type==KeyPress){ KeySym k=XLookupKeysym(&e.xkey,0); if(k==XK_Escape){closed=1;break;} if(k==XK_w)key_w=1;else if(k==XK_s)key_s=1;else if(k==XK_a)key_a=1;else if(k==XK_d)key_d=1; else if(k>=XK_F1&&k<=XK_F12)next.ack_index=(int)(k-XK_F1); else if(f.phase==PHASE_TERMINAL){ if(k==XK_Return)next.enter=1; else { char buf[8]; KeySym ks; int n=XLookupString(&e.xkey,buf,sizeof(buf),&ks,NULL); if(n>0)next.typed_char=(unsigned char)buf[0]; }} }
            else if(e.type==KeyRelease){KeySym k=XLookupKeysym(&e.xkey,0); if(k==XK_w)key_w=0;else if(k==XK_s)key_s=0;else if(k==XK_a)key_a=0;else if(k==XK_d)key_d=0;}
            else if(e.type==ButtonPress&&e.xbutton.button==Button1){mouse_down=1;next.mouse_pressed=1;next.mouse_down=1;next.mouse_x=e.xbutton.x;next.mouse_y=e.xbutton.y;}
            else if(e.type==ButtonRelease&&e.xbutton.button==Button1){mouse_down=0;next.mouse_released=1;next.mouse_x=e.xbutton.x;next.mouse_y=e.xbutton.y;}
            else if(e.type==MotionNotify&&mouse_down){next.mouse_down=1;next.mouse_x=e.xmotion.x;next.mouse_y=e.xmotion.y;}
        }
        if(auto_ref) reference_next(&f,&ref,&next); else {next.forward=key_w;next.back=key_s;next.left=key_a;next.right=key_d;}
        facility_step(&f,&next); facility_input_clear(&next); next.forward=key_w;next.back=key_s;next.left=key_a;next.right=key_d; next.mouse_down=mouse_down;
        facility_render(&f,pix,FACILITY_W,FACILITY_H); XPutImage(disp,win,gc,img,0,0,0,0,FACILITY_W,FACILITY_H); XFlush(disp); if(!no_sleep)sleep_frame();
    }
    double wall=now_sec()-start; uint64_t sh=facility_state_hash(&f); if(report_path)facility_write_report(&f,report_path,wall,sh); int ok=f.success?0:1; img->data=NULL; XDestroyImage(img); free(pix); XFreeGC(disp,gc); XDestroyWindow(disp,win); XCloseDisplay(disp); return ok;
}

int main(int argc,char **argv){
    uint64_t seed=424242; double level=0.45; int headless=1,gui=0,auto_ref=0,no_sleep=0,benchmark=0,render_bench=0; const char *report=NULL,*snapshot=NULL; Difficulty d=difficulty_from_level(level);
    /* first pass difficulty so --set applies to selected level */
    for(int i=1;i<argc;i++) if(!strcmp(argv[i],"--difficulty")&&i+1<argc){ level=strtod(argv[++i],NULL); d=difficulty_from_level(level); }
    for(int i=1;i<argc;i++){
        if(!strcmp(argv[i],"--seed")&&i+1<argc)seed=strtoull(argv[++i],NULL,10);
        else if(!strcmp(argv[i],"--difficulty")){i++;}
        else if(!strcmp(argv[i],"--set")&&i+1<argc){ if(parse_set(&d,argv[++i])){fprintf(stderr,"invalid --set %s\n",argv[i]);return 2;} }
        else if(!strcmp(argv[i],"--gui")){gui=1;headless=0;}
        else if(!strcmp(argv[i],"--headless")){headless=1;gui=0;}
        else if(!strcmp(argv[i],"--auto-reference"))auto_ref=1;
        else if(!strcmp(argv[i],"--no-sleep"))no_sleep=1;
        else if(!strcmp(argv[i],"--report")&&i+1<argc)report=argv[++i];
        else if(!strcmp(argv[i],"--snapshot")&&i+1<argc)snapshot=argv[++i];
        else if(!strcmp(argv[i],"--benchmark")&&i+1<argc)benchmark=atoi(argv[++i]);
        else if(!strcmp(argv[i],"--render-benchmark")&&i+1<argc)render_bench=atoi(argv[++i]);
        else if(!strcmp(argv[i],"--help")){usage(argv[0]);return 0;}
    }
    if(benchmark>0){ double st=now_sec(); int pass=0; uint64_t agg=1469598103934665603ULL; for(int i=0;i<benchmark;i++){Facility f; int rc=run_episode(seed+(uint64_t)i,d,0,0,NULL,&f); if(!rc)pass++; uint64_t h=facility_state_hash(&f); agg^=h+0x9e3779b97f4a7c15ULL+(agg<<6)+(agg>>2);} double wall=now_sec()-st; printf("{\"mode\":\"benchmark\",\"episodes\":%d,\"passes\":%d,\"wall_seconds\":%.9f,\"episodes_per_second\":%.3f,\"aggregate_hash\":\"%016llx\"}\n",benchmark,pass,wall,benchmark/wall,(unsigned long long)agg); return pass==benchmark?0:1; }
    if(render_bench>0){ Facility f; facility_init(&f,seed,d); uint32_t *pix=calloc(FACILITY_W*FACILITY_H,sizeof(uint32_t)); double st=now_sec(); for(int i=0;i<render_bench;i++){FacilityInput in;facility_input_clear(&in);facility_step(&f,&in);if(f.done)facility_init(&f,seed,d);facility_render(&f,pix,FACILITY_W,FACILITY_H);} double wall=now_sec()-st; printf("{\"mode\":\"render_benchmark\",\"frames\":%d,\"wall_seconds\":%.9f,\"frames_per_second\":%.3f,\"frame_hash\":\"%016llx\"}\n",render_bench,wall,render_bench/wall,(unsigned long long)f.frame_hash); free(pix); return 0; }
    if(gui) return run_gui(seed,d,auto_ref,no_sleep,report);
    if(headless){ Facility f; double st=now_sec(); int rc=auto_ref?run_episode(seed,d,snapshot!=NULL,snapshot!=NULL,snapshot,&f):(facility_init(&f,seed,d),0); double wall=now_sec()-st; if(!auto_ref && snapshot){uint32_t *pix=calloc(FACILITY_W*FACILITY_H,sizeof(uint32_t));facility_render(&f,pix,FACILITY_W,FACILITY_H);facility_write_ppm(pix,FACILITY_W,FACILITY_H,snapshot);free(pix);} uint64_t sh=facility_state_hash(&f); if(report)facility_write_report(&f,report,wall,sh); else facility_write_report(&f,NULL,wall,sh); return auto_ref?rc:0; }
    return 0;
}
