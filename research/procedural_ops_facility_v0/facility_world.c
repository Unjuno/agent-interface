#define _POSIX_C_SOURCE 200809L
#include "facility.h"
#include "facility_internal.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define FNV_OFFSET 1469598103934665603ULL
#define FNV_PRIME 1099511628211ULL

double fac_clampd(double v, double lo, double hi) { return v < lo ? lo : (v > hi ? hi : v); }
static double lerp(double a, double b, double t) { return a + (b - a) * t; }
static int iround(double v) { return (int)floor(v + 0.5); }
int fac_imax(int a, int b) { return a > b ? a : b; }
int fac_imin(int a, int b) { return a < b ? a : b; }

uint64_t fac_fnv_bytes(uint64_t h, const void *data, size_t n) {
    const unsigned char *p = (const unsigned char *)data;
    for (size_t i = 0; i < n; ++i) { h ^= p[i]; h *= FNV_PRIME; }
    return h;
}
static uint64_t fnv_u64(uint64_t h, uint64_t v) { return fac_fnv_bytes(h, &v, sizeof(v)); }
static uint64_t fnv_i64(uint64_t h, int64_t v) { return fac_fnv_bytes(h, &v, sizeof(v)); }

static uint64_t rng_next(Facility *f) {
    uint64_t x = f->rng;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    f->rng = x;
    return x * 2685821657736338717ULL;
}
double fac_rng_unit(Facility *f) { return (rng_next(f) >> 11) * (1.0 / 9007199254740992.0); }
int fac_rng_int(Facility *f, int n) { return n <= 1 ? 0 : (int)(rng_next(f) % (uint64_t)n); }

Difficulty difficulty_from_level(double level) {
    double d = fac_clampd(level, 0.0, 1.0);
    Difficulty x;
    memset(&x, 0, sizeof(x));
    x.level = d;
    int map = iround(lerp(15, 31, d));
    if (!(map & 1)) map += 1;
    x.map_size = map;
    x.maze_loops = iround(lerp(18, 2, d));
    x.watcher_count = iround(lerp(2, 10, d));
    x.watcher_event_rate_hz = lerp(0.35, 2.8, d);
    x.watcher_deadline_ticks = iround(lerp(150, 34, d));
    x.track_distractors = iround(lerp(2, 10, d));
    x.track_speed_px_per_tick = lerp(0.7, 4.2, d);
    x.track_target_radius_px = lerp(13.0, 5.0, d);
    x.track_event_interval_ticks = iround(lerp(180, 55, d));
    x.track_deadline_ticks = iround(lerp(120, 26, d));
    x.code_length = iround(lerp(4, 16, d));
    x.assembly_pieces = iround(lerp(2, 7, d));
    x.assembly_tolerance_px = lerp(30.0, 7.0, d);
    x.recovery_displacement_px = lerp(35.0, 120.0, d);
    /* Global deadline is a generous reachability budget by default; sweep explicitly when studying deadline pressure. */
    x.episode_deadline_ticks = 60 * 180;
    x.fov_deg = lerp(74.0, 64.0, d);
    return x;
}
int difficulty_set(Difficulty *d, const char *key, double value) {
    if (!strcmp(key, "map_size")) { int v=(int)value; if (v<9||v>FACILITY_MAX_MAP) return -1; if(!(v&1)) v++; d->map_size=v; return 0; }
    if (!strcmp(key, "maze_loops")) { if(value<0||value>200) return -1; d->maze_loops=(int)value; return 0; }
    if (!strcmp(key, "watcher_count")) { if(value<1||value>FACILITY_MAX_WATCHERS) return -1; d->watcher_count=(int)value; return 0; }
    if (!strcmp(key, "watcher_event_rate_hz")) { if(value<=0||value>60) return -1; d->watcher_event_rate_hz=value; return 0; }
    if (!strcmp(key, "watcher_deadline_ticks")) { if(value<1) return -1; d->watcher_deadline_ticks=(int)value; return 0; }
    if (!strcmp(key, "track_distractors")) { if(value<0||value>FACILITY_MAX_TRACK_OBJECTS-1) return -1; d->track_distractors=(int)value; return 0; }
    if (!strcmp(key, "track_speed_px_per_tick")) { if(value<0||value>50) return -1; d->track_speed_px_per_tick=value; return 0; }
    if (!strcmp(key, "track_target_radius_px")) { if(value<2||value>40) return -1; d->track_target_radius_px=value; return 0; }
    if (!strcmp(key, "track_event_interval_ticks")) { if(value<1) return -1; d->track_event_interval_ticks=(int)value; return 0; }
    if (!strcmp(key, "track_deadline_ticks")) { if(value<1) return -1; d->track_deadline_ticks=(int)value; return 0; }
    if (!strcmp(key, "code_length")) { if(value<1||value>FACILITY_CODE_MAX) return -1; d->code_length=(int)value; return 0; }
    if (!strcmp(key, "assembly_pieces")) { if(value<1||value>FACILITY_MAX_ASSEMBLY) return -1; d->assembly_pieces=(int)value; return 0; }
    if (!strcmp(key, "assembly_tolerance_px")) { if(value<=0||value>80) return -1; d->assembly_tolerance_px=value; return 0; }
    if (!strcmp(key, "recovery_displacement_px")) { if(value<0||value>200) return -1; d->recovery_displacement_px=value; return 0; }
    if (!strcmp(key, "episode_deadline_ticks")) { if(value<60) return -1; d->episode_deadline_ticks=(int)value; return 0; }
    if (!strcmp(key, "fov_deg")) { if(value<30||value>120) return -1; d->fov_deg=value; return 0; }
    return -1;
}

void fac_hash_event(Facility *f, uint64_t tag, int a, int b) {
    f->event_hash = fnv_u64(f->event_hash, tag);
    f->event_hash = fnv_i64(f->event_hash, a);
    f->event_hash = fnv_i64(f->event_hash, b);
    f->event_hash = fnv_i64(f->event_hash, f->tick);
}

static int open_cell(const Facility *f, int x, int y) {
    return x >= 0 && y >= 0 && x < f->map_w && y < f->map_h && f->map[y][x] == 0;
}

static void generate_maze(Facility *f) {
    int n = f->d.map_size;
    if (!(n & 1)) n++;
    if (n > FACILITY_MAX_MAP) n = FACILITY_MAX_MAP;
    f->map_w = f->map_h = n;
    for (int y=0;y<n;y++) for(int x=0;x<n;x++) f->map[y][x]=1;
    int sx[FACILITY_MAX_PATH], sy[FACILITY_MAX_PATH], top=0;
    int cx=1, cy=1;
    f->map[cy][cx]=0;
    sx[top]=cx; sy[top]=cy; top++;
    const int dx[4]={2,-2,0,0}, dy[4]={0,0,2,-2};
    while(top>0){
        cx=sx[top-1]; cy=sy[top-1];
        int opts[4], count=0;
        for(int k=0;k<4;k++){
            int nx=cx+dx[k], ny=cy+dy[k];
            if(nx>0&&ny>0&&nx<n-1&&ny<n-1&&f->map[ny][nx]) opts[count++]=k;
        }
        if(!count){ top--; continue; }
        int k=opts[fac_rng_int(f,count)];
        int nx=cx+dx[k], ny=cy+dy[k];
        f->map[cy+dy[k]/2][cx+dx[k]/2]=0;
        f->map[ny][nx]=0;
        sx[top]=nx; sy[top]=ny; top++;
    }
    /* Add a controlled number of loops without disconnecting the maze. */
    for(int i=0;i<f->d.maze_loops;i++){
        int x=1+fac_rng_int(f,n-2), y=1+fac_rng_int(f,n-2);
        if(f->map[y][x]==0) continue;
        int horiz=(x>0&&x<n-1&&open_cell(f,x-1,y)&&open_cell(f,x+1,y));
        int vert=(y>0&&y<n-1&&open_cell(f,x,y-1)&&open_cell(f,x,y+1));
        if(horiz||vert) f->map[y][x]=0;
    }
    f->start_cx=1; f->start_cy=1;
}

static void bfs_terminal_and_path(Facility *f) {
    int n=f->map_w;
    static int dist[FACILITY_MAX_MAP][FACILITY_MAX_MAP];
    static int px[FACILITY_MAX_MAP][FACILITY_MAX_MAP];
    static int py[FACILITY_MAX_MAP][FACILITY_MAX_MAP];
    int qx[FACILITY_MAX_PATH], qy[FACILITY_MAX_PATH], qh=0, qt=0;
    for(int y=0;y<n;y++) for(int x=0;x<n;x++){ dist[y][x]=-1; px[y][x]=-1; py[y][x]=-1; }
    dist[f->start_cy][f->start_cx]=0; qx[qt]=f->start_cx; qy[qt]=f->start_cy; qt++;
    const int dx[4]={1,-1,0,0}, dy[4]={0,0,1,-1};
    int bx=f->start_cx, by=f->start_cy;
    while(qh<qt){
        int x=qx[qh], y=qy[qh++];
        if(dist[y][x]>dist[by][bx]){ bx=x; by=y; }
        for(int k=0;k<4;k++){
            int nx=x+dx[k], ny=y+dy[k];
            if(open_cell(f,nx,ny)&&dist[ny][nx]<0){
                dist[ny][nx]=dist[y][x]+1; px[ny][nx]=x; py[ny][nx]=y;
                qx[qt]=nx; qy[qt]=ny; qt++;
            }
        }
    }
    f->terminal_cx=bx; f->terminal_cy=by;
    int rx[FACILITY_MAX_PATH], ry[FACILITY_MAX_PATH], len=0;
    int x=bx,y=by;
    while(!(x==f->start_cx&&y==f->start_cy) && len<FACILITY_MAX_PATH){
        rx[len]=x; ry[len]=y; len++;
        int nx=px[y][x], ny=py[y][x]; x=nx; y=ny;
    }
    rx[len]=f->start_cx; ry[len]=f->start_cy; len++;
    f->path_len=len;
    for(int i=0;i<len;i++){ f->path_x[i]=rx[len-1-i]; f->path_y[i]=ry[len-1-i]; }
}

int fac_watcher_interval(Facility *f) {
    double rate=f->d.watcher_event_rate_hz;
    int mean=(int)floor(60.0/rate);
    int jitter=fac_imax(1, mean/2);
    return fac_imax(8, mean-jitter + fac_rng_int(f, 2*jitter+1));
}

static void init_watchers(Facility *f) {
    for(int i=0;i<f->d.watcher_count;i++){
        f->watchers[i].active=0;
        f->watchers[i].generation=0;
        f->watchers[i].last_resolved_generation=0;
        f->watchers[i].next_tick=18 + i*5 + fac_watcher_interval(f);
        f->watchers[i].deadline_tick=0;
    }
}

static void init_track(Facility *f) {
    f->track_count=1+f->d.track_distractors;
    if(f->track_count>FACILITY_MAX_TRACK_OBJECTS) f->track_count=FACILITY_MAX_TRACK_OBJECTS;
    for(int i=0;i<f->track_count;i++){
        TrackObject *o=&f->track[i];
        o->x=26 + fac_rng_unit(f)*118;
        o->y=26 + fac_rng_unit(f)*68;
        double a=fac_rng_unit(f)*2*M_PI;
        double s=f->d.track_speed_px_per_tick*(0.65+0.35*fac_rng_unit(f));
        o->vx=cos(a)*s; o->vy=sin(a)*s;
        o->color=fac_rng_int(f,6); o->shape=fac_rng_int(f,4);
    }
    f->track_authoritative=fac_rng_int(f,f->track_count);
    f->track_previous_authoritative=-1;
    f->track_active=0;
    f->track_generation=0;
    f->track_next_event_tick=45 + f->d.track_event_interval_ticks;
}

static void init_code(Facility *f) {
    static const char alpha[]="ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    int n=fac_imin(f->d.code_length,FACILITY_CODE_MAX);
    for(int i=0;i<n;i++) f->code[i]=alpha[fac_rng_int(f,(int)strlen(alpha))];
    f->code[n]='\0'; f->typed[0]='\0'; f->typed_len=0;
}

static void init_assembly(Facility *f) {
    f->piece_count=f->d.assembly_pieces;
    if(f->piece_count>FACILITY_MAX_ASSEMBLY) f->piece_count=FACILITY_MAX_ASSEMBLY;
    for(int i=0;i<f->piece_count;i++){
        AssemblyPiece *p=&f->pieces[i];
        p->x=60 + (i%4)*70;
        p->y=160 + (i/4)*72;
        p->slot_x=385 + (i%4)*58;
        p->slot_y=150 + (i/4)*82;
        p->color=i%6; p->shape=i%4; p->placed=0;
    }
    f->dragging_piece=-1;
}

int facility_init(Facility *f, uint64_t seed, Difficulty d) {
    memset(f,0,sizeof(*f));
    f->seed=seed; f->d=d; f->rng=seed ? seed : 0x9e3779b97f4a7c15ULL;
    f->event_hash=FNV_OFFSET; f->input_hash=FNV_OFFSET;
    generate_maze(f);
    bfs_terminal_and_path(f);
    f->player_x=f->start_cx+0.5; f->player_y=f->start_cy+0.5;
    if(f->path_len>1) f->player_angle=atan2((f->path_y[1]+0.5)-f->player_y,(f->path_x[1]+0.5)-f->player_x);
    f->player_speed=0.075;
    f->phase=PHASE_NAV; f->phase_tick=0;
    init_watchers(f); init_track(f); init_code(f); init_assembly(f);
    fac_hash_event(f,1,(int)(seed&0x7fffffff),f->map_w);
    return 0;
}

void facility_input_clear(FacilityInput *in) { memset(in,0,sizeof(*in)); in->ack_index=-1; }

double fac_wrap_angle(double a){ while(a>M_PI)a-=2*M_PI; while(a<-M_PI)a+=2*M_PI; return a; }

static int collides(const Facility *f, double x, double y) {
    int cx=(int)floor(x), cy=(int)floor(y);
    return !open_cell(f,cx,cy);
}

void fac_apply_movement(Facility *f, const FacilityInput *in) {
    f->player_angle=fac_wrap_angle(f->player_angle+in->turn_delta);
    double forward=(in->forward?1.0:0.0)-(in->back?1.0:0.0);
    double strafe=(in->right?1.0:0.0)-(in->left?1.0:0.0);
    double vx=cos(f->player_angle)*forward + cos(f->player_angle+M_PI/2)*strafe;
    double vy=sin(f->player_angle)*forward + sin(f->player_angle+M_PI/2)*strafe;
    double norm=hypot(vx,vy); if(norm>1){vx/=norm;vy/=norm;}
    double nx=f->player_x+vx*f->player_speed, ny=f->player_y+vy*f->player_speed;
    if(!collides(f,nx,f->player_y)) f->player_x=nx;
    if(!collides(f,f->player_x,ny)) f->player_y=ny;
}

void fac_schedule_watcher(Facility *f, int i) { f->watchers[i].next_tick=f->tick+fac_watcher_interval(f); }
