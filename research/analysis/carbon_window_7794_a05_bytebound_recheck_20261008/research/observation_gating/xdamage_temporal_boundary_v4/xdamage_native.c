#define _GNU_SOURCE
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <dlfcn.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
typedef XID Damage;
typedef Bool (*QueryFn)(Display*,int*,int*);
typedef Damage (*CreateFn)(Display*,Drawable,int);
typedef void (*SubtractFn)(Display*,Damage,XID,XID);
typedef void (*DestroyFn)(Display*,Damage);
typedef struct {int type;unsigned long serial;Bool send_event;Display*display;Drawable drawable;Damage damage;Time timestamp;XRectangle area;XRectangle geometry;} DamageEvent;
static void fatal(const char*s){fprintf(stderr,"%s: %s\n",s,strerror(errno));exit(2);}
static Display* open_display(void){Display*d=XOpenDisplay(NULL);if(!d){fprintf(stderr,"XOpenDisplay failed\n");exit(2);}return d;}
static uint8_t channel(unsigned long p,unsigned long m){if(!m)return 0;unsigned s=__builtin_ctzl(m);unsigned long max=m>>s;return (uint8_t)((((p&m)>>s)*255+max/2)/max);}
static void capture(Display*d,Window w,const char*path){XWindowAttributes a;if(!XGetWindowAttributes(d,w,&a)){fprintf(stderr,"XGetWindowAttributes failed\n");exit(3);}XImage*i=XGetImage(d,w,0,0,64,64,AllPlanes,ZPixmap);if(!i){fprintf(stderr,"XGetImage failed\n");exit(3);}FILE*f=fopen(path,"wb");if(!f)fatal("fopen frame");for(int y=0;y<64;y++)for(int x=0;x<64;x++){unsigned long p=XGetPixel(i,x,y);uint8_t rgb[3]={channel(p,a.visual->red_mask),channel(p,a.visual->green_mask),channel(p,a.visual->blue_mask)};if(fwrite(rgb,1,3,f)!=3)fatal("write frame");}if(fclose(f))fatal("close frame");XDestroyImage(i);}
static int render(int kind,int undo,unsigned long xid){Display*d=open_display();Window w=(Window)xid;GC g=XCreateGC(d,w,0,NULL);if(!g){fprintf(stderr,"XCreateGC failed\n");return 3;}int n=kind==3?1:kind==4?2:kind==5?8:64;if(kind==0){}else if(kind==1){XSetForeground(d,g,0);XFillRectangle(d,w,g,0,0,64,64);}else if(kind==2){XSetForeground(d,g,0xffffff);XFillRectangle(d,w,g,0,0,64,64);}else{XSetForeground(d,g,undo?0:0xffffff);XFillRectangle(d,w,g,0,0,n,n);}XSync(d,False);XFreeGC(d,g);XCloseDisplay(d);return 0;}
static pid_t launch_renderer(int kind,int undo,unsigned long xid,int*exitcode){pid_t p=fork();if(p<0)fatal("fork");if(p==0){char a[16],b[16],c[32];snprintf(a,sizeof a,"%d",kind);snprintf(b,sizeof b,"%d",undo);snprintf(c,sizeof c,"%lu",xid);execl("/proc/self/exe","xdamage_native","render",a,b,c,(char*)NULL);_exit(127);}int st;while(waitpid(p,&st,0)<0){if(errno==EINTR)continue;fatal("waitpid");}*exitcode=WIFEXITED(st)?WEXITSTATUS(st):128+WTERMSIG(st);return p;}
static int observe(int kind,const char*prefix){void*lib=dlopen("libXdamage.so.1",RTLD_NOW);if(!lib){fprintf(stderr,"dlopen: %s\n",dlerror());return 2;}QueryFn query=(QueryFn)dlsym(lib,"XDamageQueryExtension");CreateFn create=(CreateFn)dlsym(lib,"XDamageCreate");SubtractFn subtract=(SubtractFn)dlsym(lib,"XDamageSubtract");DestroyFn destroy=(DestroyFn)dlsym(lib,"XDamageDestroy");if(!query||!create||!subtract||!destroy){fprintf(stderr,"missing libXdamage symbol\n");return 2;}Display*d=open_display();int eb,er;if(!query(d,&eb,&er)){fprintf(stderr,"XDamage extension unavailable\n");return 2;}Window w=XCreateSimpleWindow(d,DefaultRootWindow(d),0,0,64,64,0,0,0);XMapWindow(d,w);XSync(d,False);GC gc=XCreateGC(d,w,0,NULL);XSetForeground(d,gc,0);XFillRectangle(d,w,gc,0,0,64,64);XSync(d,False);Damage dm=create(d,w,3);XSync(d,False);subtract(d,dm,None,None);XSync(d,False);while(XPending(d)){XEvent x;XNextEvent(d,&x);}char path[512];snprintf(path,sizeof path,"%s_baseline.rgb",prefix);capture(d,w,path);int midexit=0,endexit=0;pid_t midpid=launch_renderer(kind,0,w,&midexit);snprintf(path,sizeof path,"%s_middle.rgb",prefix);capture(d,w,path);pid_t endpid=0;if(kind>=3){endpid=launch_renderer(kind,1,w,&endexit);}snprintf(path,sizeof path,"%s_endpoint.rgb",prefix);capture(d,w,path);XSync(d,False);int count=0;unsigned long evserial=0,evtime=0,evdraw=0,evid=0;while(XPending(d)){XEvent x;XNextEvent(d,&x);if(x.type==eb){DamageEvent*n=(DamageEvent*)&x;if(n->drawable==w&&n->damage==dm){count++;evserial=n->serial;evtime=n->timestamp;evdraw=n->drawable;evid=n->damage;}}}printf("{\"observer_pid\":%ld,\"window\":%lu,\"damage_id\":%lu,\"damage_event_type\":%d,\"damage_count\":%d,\"event_serial\":%lu,\"event_time\":%lu,\"event_drawable\":%lu,\"event_damage\":%lu,\"renderer_middle_pid\":%ld,\"renderer_middle_exit\":%d,\"renderer_endpoint_pid\":%ld,\"renderer_endpoint_exit\":%d}\n",(long)getpid(),w,(unsigned long)dm,eb,count,evserial,evtime,evdraw,evid,(long)midpid,midexit,(long)endpid,endexit);fflush(stdout);destroy(d,dm);XFreeGC(d,gc);XDestroyWindow(d,w);XSync(d,False);XCloseDisplay(d);return (midexit||endexit)?5:0;}
int main(int ac,char**av){if(ac>=2&&!strcmp(av[1],"render")){if(ac!=5)return 2;return render(atoi(av[2]),atoi(av[3]),strtoul(av[4],NULL,10));}if(ac!=4||strcmp(av[1],"observe"))return 2;return observe(atoi(av[2]),av[3]);}
