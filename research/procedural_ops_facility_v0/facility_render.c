#define _POSIX_C_SOURCE 200809L
#include "facility.h"
#include <math.h>
#include <stdint.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
#define FNV_OFFSET 1469598103934665603ULL
#define FNV_PRIME 1099511628211ULL
static int r_imax(int a,int b){return a>b?a:b;}
static int r_imin(int a,int b){return a<b?a:b;}
static double r_clamp(double v,double lo,double hi){return v<lo?lo:(v>hi?hi:v);}
static double r_wrap(double a){while(a>M_PI)a-=2*M_PI;while(a<-M_PI)a+=2*M_PI;return a;}
static uint64_t r_fnv(uint64_t h,const void *data,size_t n){const unsigned char*p=data;for(size_t i=0;i<n;i++){h^=p[i];h*=FNV_PRIME;}return h;}

/* ---------- software renderer ---------- */
static uint32_t rgb(unsigned r,unsigned g,unsigned b){ return 0xff000000u | ((r&255)<<16)|((g&255)<<8)|(b&255); }
static void fill_rect(uint32_t *p,int w,int h,int x0,int y0,int x1,int y1,uint32_t c){
    x0=r_imax(0,x0);y0=r_imax(0,y0);x1=r_imin(w,x1);y1=r_imin(h,y1); for(int y=y0;y<y1;y++) for(int x=x0;x<x1;x++)p[y*w+x]=c;
}
static void circle(uint32_t *p,int w,int h,int cx,int cy,int r,uint32_t c){
    for(int y=cy-r;y<=cy+r;y++) if(y>=0&&y<h) for(int x=cx-r;x<=cx+r;x++) if(x>=0&&x<w){int dx=x-cx,dy=y-cy;if(dx*dx+dy*dy<=r*r)p[y*w+x]=c;}
}
static void draw_digit(uint32_t *p,int w,int h,int x,int y,int digit,uint32_t c){
    static const unsigned char seg[10]={0x3f,0x06,0x5b,0x4f,0x66,0x6d,0x7d,0x07,0x7f,0x6f}; unsigned s=seg[digit%10];
    int t=2,L=8; if(s&1)fill_rect(p,w,h,x+2,y,x+L,y+t,c); if(s&2)fill_rect(p,w,h,x+L,y+2,x+L+t,y+L,c); if(s&4)fill_rect(p,w,h,x+L,y+L+2,x+L+t,y+2*L,c); if(s&8)fill_rect(p,w,h,x+2,y+2*L,x+L,y+2*L+t,c); if(s&16)fill_rect(p,w,h,x,y+L+2,x+t,y+2*L,c); if(s&32)fill_rect(p,w,h,x,y+2,x+t,y+L,c); if(s&64)fill_rect(p,w,h,x+2,y+L,x+L,y+L+t,c);
}
static uint32_t palette(int i){ static const uint32_t c[]={0xff3b82f6,0xffef4444,0xff22c55e,0xffeab308,0xffa855f7,0xfff97316}; return c[i%6]; }

static void render_world(Facility *f,uint32_t *pix,int w,int h){
    int top=58, vh=h-top;
    fill_rect(pix,w,h,0,top,w,top+vh/2,rgb(30,38,50)); fill_rect(pix,w,h,0,top+vh/2,w,h,rgb(21,28,36));
    double fov=f->d.fov_deg*M_PI/180.0;
    double zbuf[FACILITY_W];
    int rw=r_imin(w,FACILITY_W);
    for(int x=0;x<rw;x++){
        double cam=(2.0*x/(double)rw)-1.0; double a=f->player_angle+atan(cam*tan(fov/2));
        double rayx=cos(a),rayy=sin(a),px=f->player_x,py=f->player_y;
        int mx=(int)px,my=(int)py; double ddx=fabs(1.0/(fabs(rayx)<1e-9?1e-9:rayx)), ddy=fabs(1.0/(fabs(rayy)<1e-9?1e-9:rayy));
        int sx=rayx<0?-1:1, sy=rayy<0?-1:1; double sdx=(rayx<0?(px-mx):(mx+1.0-px))*ddx, sdy=(rayy<0?(py-my):(my+1.0-py))*ddy; int side=0;
        for(int guard=0;guard<128;guard++){ if(sdx<sdy){sdx+=ddx;mx+=sx;side=0;}else{sdy+=ddy;my+=sy;side=1;} if(mx<0||my<0||mx>=f->map_w||my>=f->map_h||f->map[my][mx])break; }
        double dist=side==0?(mx-px+(1-sx)/2.0)/(rayx==0?1e-9:rayx):(my-py+(1-sy)/2.0)/(rayy==0?1e-9:rayy); if(dist<0.05)dist=0.05; zbuf[x]=dist;
        int line=(int)(vh/dist); int y0=top+vh/2-line/2,y1=top+vh/2+line/2; unsigned shade=(unsigned)r_clamp(190.0/(1+dist*0.11),48,170); if(side)shade=(unsigned)(shade*0.78); uint32_t col=rgb(shade,shade+8,shade+16); fill_rect(pix,w,h,x,y0,x+1,y1,col);
    }
    /* Terminal as a billboard at destination. */
    double dx=(f->terminal_cx+0.5)-f->player_x,dy=(f->terminal_cy+0.5)-f->player_y,dist=hypot(dx,dy),rel=r_wrap(atan2(dy,dx)-f->player_angle);
    if(fabs(rel)<fov*0.58 && dist>0.1){ int sx=(int)(rw*0.5 + tan(rel)/(tan(fov/2))*rw*0.5); int size=(int)(110.0/dist); if(size<4)size=4; if(size>120)size=120; int depthx=r_imin(r_imax(sx,0),rw-1); if(dist<zbuf[depthx]+0.25){ fill_rect(pix,w,h,sx-size/2,top+vh/2-size/2,sx+size/2,top+vh/2+size/2,rgb(17,88,110)); fill_rect(pix,w,h,sx-size/3,top+vh/2-size/4,sx+size/3,top+vh/2+size/4,rgb(34,211,238)); }}
}
static void render_watchers(Facility *f,uint32_t *pix,int w,int h){
    int tile=38,gap=4,x=8,y=8; for(int i=0;i<f->d.watcher_count;i++){
        uint32_t c=f->watchers[i].active?rgb(248,113,113):rgb(51,65,85); fill_rect(pix,w,h,x+i*(tile+gap),y,x+i*(tile+gap)+tile,y+tile,c); draw_digit(pix,w,h,x+i*(tile+gap)+13,y+8,(i+1)%10,rgb(248,250,252));
    }
}

static void render_track(Facility *f,uint32_t *pix,int w,int h){
    if(f->phase!=PHASE_NAV) return;
    int ox=w-174,oy=h-114;
    fill_rect(pix,w,h,ox-4,oy-4,ox+164,oy+104,rgb(15,23,42));
    uint32_t border=f->track_active?rgb(34,197,94):rgb(245,158,11);
    fill_rect(pix,w,h,ox-4,oy-4,ox+164,oy,border); fill_rect(pix,w,h,ox-4,oy+100,ox+164,oy+104,border); fill_rect(pix,w,h,ox-4,oy,ox,oy+100,border); fill_rect(pix,w,h,ox+160,oy,ox+164,oy+100,border);
    int a=f->track_authoritative; circle(pix,w,h,ox+18,oy+18,8,palette(f->track[a].color));
    for(int i=0;i<f->track_count;i++){ int r=(int)f->d.track_target_radius_px; uint32_t c=palette(f->track[i].color); if(f->track[i].shape==1) fill_rect(pix,w,h,(int)(ox+f->track[i].x-r),(int)(oy+f->track[i].y-r),(int)(ox+f->track[i].x+r),(int)(oy+f->track[i].y+r),c); else circle(pix,w,h,(int)(ox+f->track[i].x),(int)(oy+f->track[i].y),r,c); }
}

static void render_terminal(Facility *f,uint32_t *pix,int w,int h){
    fill_rect(pix,w,h,0,58,w,h,rgb(17,24,39)); int n=(int)strlen(f->code); int cardw=r_imax(160,20*n); int x=(w-cardw)/2; fill_rect(pix,w,h,x,80,x+cardw,132,rgb(30,41,59));
    /* Render code deterministically as byte bars; the X11 version need not depend on fonts. */
    for(int i=0;i<n;i++){ unsigned v=(unsigned char)f->code[i]; int bx=x+10+i*18; for(int b=0;b<6;b++) if(v&(1u<<b)) fill_rect(pix,w,h,bx,90+b*6,bx+12,94+b*6,rgb(226,232,240)); }
    fill_rect(pix,w,h,140,185,w-140,245,rgb(31,41,55)); fill_rect(pix,w,h,146,191,w-146,239,rgb(15,23,42));
    for(int i=0;i<f->typed_len;i++){ unsigned v=(unsigned char)f->typed[i]; int bx=155+i*18; for(int b=0;b<6;b++) if(v&(1u<<b)) fill_rect(pix,w,h,bx,198+b*6,bx+12,202+b*6,rgb(74,222,128)); }
}

static void render_assembly(Facility *f,uint32_t *pix,int w,int h){
    fill_rect(pix,w,h,0,58,w,h,rgb(15,23,42)); fill_rect(pix,w,h,w/2-2,70,w/2+2,h-10,rgb(51,65,85));
    for(int i=0;i<f->piece_count;i++){ AssemblyPiece *p=&f->pieces[i]; int r=16; uint32_t c=palette(p->color); if(!p->placed){ circle(pix,w,h,(int)p->slot_x,(int)p->slot_y,r+4,rgb(71,85,105)); circle(pix,w,h,(int)p->slot_x,(int)p->slot_y,r,c&0x55ffffffu); } circle(pix,w,h,(int)p->x,(int)p->y,r,p->placed?rgb(74,222,128):c); }
}

void facility_render(Facility *f,uint32_t *pix,int w,int h){
    fill_rect(pix,w,h,0,0,w,h,rgb(2,6,23)); render_watchers(f,pix,w,h);
    if(f->phase==PHASE_NAV) { render_world(f,pix,w,h); render_watchers(f,pix,w,h); render_track(f,pix,w,h); }
    else if(f->phase==PHASE_TERMINAL) { render_terminal(f,pix,w,h); render_watchers(f,pix,w,h); }
    else if(f->phase==PHASE_ASSEMBLY) { render_assembly(f,pix,w,h); render_watchers(f,pix,w,h); }
    else { fill_rect(pix,w,h,160,140,w-160,220,rgb(30,41,59)); }
    uint64_t hsh=FNV_OFFSET; hsh=r_fnv(hsh,pix,(size_t)w*h*sizeof(uint32_t)); f->frame_hash=hsh;
}
