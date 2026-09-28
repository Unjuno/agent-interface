#define _POSIX_C_SOURCE 200809L
#include "ops_world.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define OW_FOV (M_PI / 3.0)
#define OW_PANEL_X 70
#define OW_PANEL_Y 70
#define OW_PANEL_W 500
#define OW_PANEL_H 250

#define EV_ALERT_ON 1
#define EV_ALERT_ACK 2
#define EV_ALERT_MISS 3
#define EV_PANEL_OPEN 4
#define EV_PANEL_CLOSE 5
#define EV_TARGET_HIT 6
#define EV_TERMINAL_OK 7
#define EV_TERMINAL_BAD 8
#define EV_ASSEMBLY_PLACE 9
#define EV_ASSEMBLY_MISS 10
#define EV_SUCCESS 11
#define EV_TIMEOUT 12
#define EV_WATCHER_FALSE_ACK 13
#define EV_WRONG_TARGET 14
#define EV_MOTOR_MISS 15
#define EV_TARGET_RELOCATE 16
#define EV_FORBIDDEN_ACTION 17
#define EV_RECOVERABLE_ERROR 18
#define EV_RECOVERED 19
#define EV_RECOVERY_EXHAUSTED 20
#define EV_TASK_UNLOCK 21
#define EV_EPISODE_GENERATION 22

static double mono_time(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

static uint64_t splitmix64(uint64_t *x) {
    uint64_t z = (*x += 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

static uint32_t rng_u32(OwWorld *w) {
    return (uint32_t)(splitmix64(&w->rng_state) >> 32);
}

static float rng_f01(OwWorld *w) {
    return (rng_u32(w) + 0.5f) / 4294967296.0f;
}

static float rng_range(OwWorld *w, float a, float b) {
    return a + (b - a) * rng_f01(w);
}

static int rng_int(OwWorld *w, int lo, int hi_exclusive) {
    if (hi_exclusive <= lo) return lo;
    return lo + (int)(rng_u32(w) % (uint32_t)(hi_exclusive - lo));
}

static float clampf(float v, float a, float b) {
    return v < a ? a : (v > b ? b : v);
}

static double clampd(double v, double a, double b) {
    return v < a ? a : (v > b ? b : v);
}

static void log_event(OwWorld *w, uint16_t type, int a, int b, float x, float y) {
    if (w->event_count >= OW_MAX_EVENTS) {
        w->event_overflow = 1;
        w->done = 1;
        w->success = 0;
        w->failure_code = OW_FAIL_EVENT_OVERFLOW;
        return;
    }
    OwEvent *e = &w->events[w->event_count++];
    e->t = w->sim_time;
    e->type = type;
    e->a = (int16_t)a;
    e->b = (int16_t)b;
    e->x = x;
    e->y = y;
}

static void fail_agent(OwWorld *w, uint16_t code, uint16_t event_type, int a, int b, float x, float y) {
    if (w->done) return;
    log_event(w, event_type, a, b, x, y);
    if (w->failure_code == OW_FAIL_EVENT_OVERFLOW) return;
    w->done = 1;
    w->success = 0;
    w->failure_code = code;
}

static int task_index(uint8_t bit) {
    if (bit == OW_TASK_TRANSFER) return 0;
    if (bit == OW_TASK_ASSEMBLY) return 1;
    if (bit == OW_TASK_TARGET) return 2;
    return -1;
}

static uint8_t completed_task_mask(const OwWorld *w) {
    uint8_t m = 0;
    if (w->terminal_complete) m |= OW_TASK_TRANSFER;
    if (w->assembly_complete) m |= OW_TASK_ASSEMBLY;
    if (w->target_complete) m |= OW_TASK_TARGET;
    if (w->d.required_alerts == 0 || w->alerts_acked >= w->d.required_alerts) m |= OW_TASK_ALERTS;
    return m;
}

static int task_required(const OwWorld *w, uint8_t bit) {
    return (w->task_mask & bit) != 0;
}

static int task_unlocked(const OwWorld *w, uint8_t bit) {
    if (!task_required(w, bit)) return 0;
    if (bit == OW_TASK_ALERTS) return 1;
    int idx = task_index(bit);
    if (idx < 0) return 0;
    uint8_t done = completed_task_mask(w);
    return (done & w->task_deps[idx]) == w->task_deps[idx];
}

static int task_complete(const OwWorld *w, uint8_t bit) {
    return (completed_task_mask(w) & bit) != 0;
}

static void mark_recovered(OwWorld *w, uint8_t task_bit) {
    if (!w->pending_recovery) return;
    w->pending_recovery = 0;
    ++w->recoveries;
    log_event(w, EV_RECOVERED, task_bit, (int)w->recoveries, 0, 0);
}

static void recoverable_error(OwWorld *w, int subtype, float x, float y) {
    if (w->done) return;
    ++w->recoverable_errors;
    w->pending_recovery = 1;
    log_event(w, EV_RECOVERABLE_ERROR, subtype, (int)w->recoverable_errors, x, y);
    if ((int)w->recoverable_errors > w->d.recovery_budget) {
        fail_agent(w, OW_FAIL_RECOVERY_EXHAUSTED, EV_RECOVERY_EXHAUSTED, subtype, (int)w->recoverable_errors, x, y);
    }
}

void ow_default_difficulty(OwDifficulty *d) {
    memset(d, 0, sizeof(*d));
    d->target_speed = 1.05f;
    d->object_radius = 0.18f;
    d->object_count = 10;
    d->watcher_count = 12;
    d->event_rate = 0.55f;
    d->alert_deadline = 2.5f;
    d->alert_burst = 1;
    d->required_alerts = 8;
    d->typing_length = 7;
    d->assembly_pieces = 4;
    d->assembly_tolerance = 22.0f;
    d->navigation_speed = 2.4f;
    d->mouse_gain = 0.0045f;
    d->episode_seconds = 75.0f;
    d->work_task_count = 3;
    d->dependency_depth = 1;
    d->recovery_budget = 2;
}

static int validate_ranges(const OwDifficulty *d, char *err, size_t errcap) {
#define BAD(cond, msg) do { if (cond) { if (err && errcap) snprintf(err, errcap, "%s", msg); return -1; } } while (0)
    BAD(d->target_speed < 0.0f || d->target_speed > 30.0f, "target_speed outside [0,30]");
    BAD(d->object_radius <= 0.02f || d->object_radius > 1.0f, "object_radius outside (0.02,1]");
    BAD(d->object_count < 1 || d->object_count > OW_MAX_OBJECTS, "object_count outside range");
    BAD(d->watcher_count < 0 || d->watcher_count > OW_MAX_WATCHERS, "watcher_count outside range");
    BAD(d->event_rate < 0.0f || d->event_rate > 100.0f, "event_rate outside [0,100]");
    BAD(d->alert_deadline <= 0.02f || d->alert_deadline > 60.0f, "alert_deadline outside range");
    BAD(d->alert_burst < 1 || d->alert_burst > OW_MAX_WATCHERS, "alert_burst outside range");
    BAD(d->required_alerts < 0 || d->required_alerts > 200, "required_alerts outside range");
    BAD(d->typing_length < 1 || d->typing_length >= OW_CODE_MAX, "typing_length outside range");
    BAD(d->assembly_pieces < 1 || d->assembly_pieces > OW_MAX_ASSEMBLY, "assembly_pieces outside range");
    BAD(d->assembly_tolerance <= 1.0f || d->assembly_tolerance > 100.0f, "assembly_tolerance outside range");
    BAD(d->navigation_speed <= 0.05f || d->navigation_speed > 20.0f, "navigation_speed outside range");
    BAD(d->mouse_gain <= 0.00001f || d->mouse_gain > 0.1f, "mouse_gain outside range");
    BAD(d->episode_seconds <= 1.0f || d->episode_seconds > 3600.0f, "episode_seconds outside range");
    BAD(d->work_task_count < 1 || d->work_task_count > 3, "work_task_count outside [1,3]");
    BAD(d->dependency_depth < 0 || d->dependency_depth > 2, "dependency_depth outside [0,2]");
    BAD(d->recovery_budget < 0 || d->recovery_budget > 20, "recovery_budget outside [0,20]");
#undef BAD
    if (err && errcap) err[0] = 0;
    return 0;
}

int ow_validate_difficulty(const OwDifficulty *d, char *err, size_t errcap) {
    if (validate_ranges(d, err, errcap)) return -1;
#define BAD(cond, msg) do { if (cond) { if (err && errcap) snprintf(err, errcap, "%s", msg); return -1; } } while (0)
    if (d->required_alerts > 0) {
        BAD(d->watcher_count < 1, "required_alerts > 0 requires watcher_count > 0");
        BAD(d->event_rate <= 0.0f, "required_alerts > 0 requires event_rate > 0");
        BAD(d->alert_burst > d->watcher_count, "alert_burst cannot exceed watcher_count");
        BAD(d->required_alerts > OW_MAX_ALERT_SCHEDULE, "required_alerts exceeds alert schedule capacity");
        /* event_rate is total alert arrivals/sec; burst only changes simultaneity. */
        BAD((double)d->event_rate * (double)d->alert_deadline / 0.82 > (double)d->watcher_count,
            "event_rate * alert_deadline exceeds watcher concurrency capacity");
        double worst_schedule = 0.35 + ((double)d->required_alerts / (double)d->event_rate) * 1.18 + (double)d->alert_deadline;
        BAD(worst_schedule >= (double)d->episode_seconds,
            "event schedule cannot be guaranteed inside episode budget");
    }
#undef BAD
    if (err && errcap) err[0] = 0;
    return 0;
}

int ow_set_param(OwDifficulty *d, const char *key, double v, char *err, size_t errcap) {
    OwDifficulty before = *d;
    if (!strcmp(key, "target_speed")) d->target_speed = (float)v;
    else if (!strcmp(key, "object_radius")) d->object_radius = (float)v;
    else if (!strcmp(key, "object_count")) d->object_count = (int)llround(v);
    else if (!strcmp(key, "watcher_count")) d->watcher_count = (int)llround(v);
    else if (!strcmp(key, "event_rate")) d->event_rate = (float)v;
    else if (!strcmp(key, "alert_deadline")) d->alert_deadline = (float)v;
    else if (!strcmp(key, "alert_burst")) d->alert_burst = (int)llround(v);
    else if (!strcmp(key, "required_alerts")) d->required_alerts = (int)llround(v);
    else if (!strcmp(key, "typing_length")) d->typing_length = (int)llround(v);
    else if (!strcmp(key, "assembly_pieces")) d->assembly_pieces = (int)llround(v);
    else if (!strcmp(key, "assembly_tolerance")) d->assembly_tolerance = (float)v;
    else if (!strcmp(key, "navigation_speed")) d->navigation_speed = (float)v;
    else if (!strcmp(key, "mouse_gain")) d->mouse_gain = (float)v;
    else if (!strcmp(key, "episode_seconds")) d->episode_seconds = (float)v;
    else if (!strcmp(key, "work_task_count")) d->work_task_count = (int)llround(v);
    else if (!strcmp(key, "dependency_depth")) d->dependency_depth = (int)llround(v);
    else if (!strcmp(key, "recovery_budget")) d->recovery_budget = (int)llround(v);
    else {
        if (err && errcap) snprintf(err, errcap, "unknown parameter: %s", key);
        return -1;
    }
    if (validate_ranges(d, err, errcap)) { *d = before; return -1; }
    return 0;
}

static const char *BASE_MAP[OW_MAP_H] = {
    "####################",
    "#......#...........#",
    "#......#...........#",
    "#..................#",
    "#......#...........#",
    "#......#...........#",
    "#......#####.#######",
    "#..................#",
    "#..................#",
    "####.########......#",
    "#..................#",
    "#..................#",
    "#......#####.......#",
    "#..................#",
    "#..................#",
    "#...#..............#",
    "#...#......#.......#",
    "#..........#.......#",
    "#..................#",
    "####################",
};

static int wall_at(const OwWorld *w, float x, float y) {
    int ix=(int)floorf(x),iy=(int)floorf(y);
    if(ix<0||iy<0||ix>=OW_MAP_W||iy>=OW_MAP_H)return 1;
    return w->map[iy][ix]!=0;
}

static int visible_line(const OwWorld *w, float x0, float y0, float x1, float y1) {
    float dx=x1-x0,dy=y1-y0,dist=hypotf(dx,dy);
    int steps=(int)(dist*18.0f)+1;
    for(int i=1;i<steps;++i){
        float t=(float)i/(float)steps;
        if(wall_at(w,x0+dx*t,y0+dy*t))return 0;
    }
    return 1;
}

/* 8 topology-preserving symmetries of the square around the 20x20 map. */
static void map_source_xy(int variant, int x, int y, int *sx, int *sy) {
    int n=OW_MAP_W-1;
    switch(variant&7){
    case 0:*sx=x;*sy=y;break;
    case 1:*sx=n-y;*sy=x;break;
    case 2:*sx=n-x;*sy=n-y;break;
    case 3:*sx=y;*sy=n-x;break;
    case 4:*sx=n-x;*sy=y;break;
    case 5:*sx=x;*sy=n-y;break;
    case 6:*sx=y;*sy=x;break;
    default:*sx=n-y;*sy=n-x;break;
    }
}

static int opening_candidate_index(int sx, int sy) {
    /* Interior walls that can be opened without touching the border. */
    static const int p[][2]={{7,2},{7,4},{10,6},{4,9},{8,9},{12,9},{7,12},{11,16},{4,17},{10,17},{14,6},{4,15}};
    for(int i=0;i<(int)(sizeof(p)/sizeof(p[0]));++i)if(p[i][0]==sx&&p[i][1]==sy)return i;
    return -1;
}

static void init_map(OwWorld *w) {
    w->map_variant=(uint8_t)rng_int(w,0,8);
    w->map_openings_mask=(uint16_t)(rng_u32(w)&0x0fffu);
    for(int y=0;y<OW_MAP_H;++y)for(int x=0;x<OW_MAP_W;++x){
        int sx,sy;map_source_xy(w->map_variant,x,y,&sx,&sy);
        int solid=BASE_MAP[sy][sx]=='#';
        if(solid&&sx>0&&sy>0&&sx<OW_MAP_W-1&&sy<OW_MAP_H-1){int k=opening_candidate_index(sx,sy);if(k>=0&&(w->map_openings_mask&(1u<<k)))solid=0;}
        w->map[y][x]=(uint8_t)solid;
    }
}

static void collect_free_cells(const OwWorld *w, int cells[][2], int *count) {
    int n=0;
    for(int y=1;y<OW_MAP_H-1;++y)for(int x=1;x<OW_MAP_W-1;++x){
        if(w->map[y][x])continue;
        int open=0;
        if(!w->map[y-1][x]) open++;
        if(!w->map[y+1][x]) open++;
        if(!w->map[y][x-1]) open++;
        if(!w->map[y][x+1]) open++;
        if(open>=2){cells[n][0]=x;cells[n][1]=y;++n;}
    }
    *count=n;
}

static void shuffle_cells(OwWorld *w, int cells[][2], int n) {
    for(int i=n-1;i>0;--i){int j=rng_int(w,0,i+1);int tx=cells[i][0],ty=cells[i][1];cells[i][0]=cells[j][0];cells[i][1]=cells[j][1];cells[j][0]=tx;cells[j][1]=ty;}
}

static int compare_double(const void *aa, const void *bb) {
    const double *a=(const double*)aa,*b=(const double*)bb;
    return (*a>*b)-(*a<*b);
}

