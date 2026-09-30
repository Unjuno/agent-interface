#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
typedef XID Damage;
typedef Bool (*QueryFn)(Display*,int*,int*);
typedef Damage (*CreateFn)(Display*,Drawable,int);
typedef void (*SubtractFn)(Display*,Damage,XID,XID);
typedef void (*DestroyFn)(Display*,Damage);
typedef struct {int type;unsigned long serial;Bool send_event;Display*display;Drawable drawable;Damage damage;Time timestamp;XRectangle area;XRectangle geometry;} DamageEvent;
static void die(const char*s){perror(s);exit(2);}
static uint8_t ch(unsigned long p,unsigned long m){if(!m)return 0;unsigned s=__builtin_ctzl(m);unsigned long z=m>>s;return (uint8_t)((((p&m)>>s)*255+z/2)/z);}
static void snap(Display*d,Window w,uint8_t*out){XWindowAttributes a;if(!XGetWindowAttributes(d,w,&a))exit(3);XImage*i=XGetImage(d,w,0,0,64,64,AllPlanes,ZPixmap);if(!i)exit(3);for(int y=0;y<64;y++)for(int x=0;x<64;x++){unsigned long q=XGetPixel(i,x,y);int k=(y*64+x)*3;out[k]=ch(q,a.visual->red_mask);out[k+1]=ch(q,a.visual->green_mask);out[k+2]=ch(q,a.visual->blue_mask);}XDestroyImage(i);}
static void fill(Display*d,Window w,GC g,unsigned long px,int n){XSetForeground(d,g,px);XFillRectangle(d,w,g,0,0,n,n);XSync(d,False);}
int main(){void*l=dlopen("libXdamage.so.1",RTLD_NOW);if(!l){fprintf(stderr,"%s\n",dlerror());return 2;}QueryFn query=(QueryFn)dlsym(l,"XDamageQueryExtension");CreateFn create=(CreateFn)dlsym(l,"XDamageCreate");SubtractFn subtract=(SubtractFn)dlsym(l,"XDamageSubtract");DestroyFn destroy=(DestroyFn)dlsym(l,"XDamageDestroy");Display*d=XOpenDisplay(NULL);if(!d)return 2;int eb,er;if(!query(d,&eb,&er))return 2;int counts[6]={0};const char*names[]={"QUIET","REPAINT_A","PERSIST_B","ABA_1PX","ABA_2X2","ABA_8X8"};
 for(int k=0;k<6;k++){Window w=XCreateSimpleWindow(d,DefaultRootWindow(d),0,0,64,64,0,0,0);XMapWindow(d,w);XSync(d,False);GC g=XCreateGC(d,w,0,NULL);fill(d,w,g,0,64);Damage dm=create(d,w,3);XSync(d,False);subtract(d,dm,None,None);XSync(d,False);while(XPending(d)){XEvent init;XNextEvent(d,&init);}uint8_t b[12288],m[12288],e[12288];snap(d,w,b);
 if(k==1)fill(d,w,g,0,64); if(k==2)fill(d,w,g,0xffffff,64);if(k>=3){int n=k==3?1:k==4?2:8;fill(d,w,g,0xffffff,n);}snap(d,w,m);
 if(k==2){}else if(k==1){}else if(k>=3){int n=k==3?1:k==4?2:8;fill(d,w,g,0,n);}snap(d,w,e);XSync(d,False);while(XPending(d)){XEvent x;XNextEvent(d,&x);if(x.type==eb){DamageEvent*q=(DamageEvent*)&x;if(q->drawable==w&&q->damage==dm)counts[k]++;}}
 FILE*f;char p[128];snprintf(p,sizeof p,"/results/formal01/construction_%s.rgb",names[k]);f=fopen(p,"wb");if(!f)die("fopen");fwrite(b,1,sizeof b,f);fwrite(m,1,sizeof m,f);fwrite(e,1,sizeof e,f);fclose(f);int md=memcmp(b,m,sizeof b)!=0,ed=memcmp(b,e,sizeof b)!=0;printf("%s middle_diff=%d endpoint_diff=%d damage_events=%d\n",names[k],md,ed,counts[k]);destroy(d,dm);XFreeGC(d,g);XDestroyWindow(d,w);XSync(d,False);}
 XCloseDisplay(d);return 0;}









