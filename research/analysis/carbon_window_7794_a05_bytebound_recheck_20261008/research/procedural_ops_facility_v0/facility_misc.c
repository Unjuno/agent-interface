#define _POSIX_C_SOURCE 200809L
#include "facility.h"
#include <math.h>
#include <stdio.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
#define FNV_OFFSET 1469598103934665603ULL
#define FNV_PRIME 1099511628211ULL
static uint64_t m_fnv_bytes(uint64_t h,const void*data,size_t n){const unsigned char*p=data;for(size_t i=0;i<n;i++){h^=p[i];h*=FNV_PRIME;}return h;}
static uint64_t m_fnv_u64(uint64_t h,uint64_t v){return m_fnv_bytes(h,&v,sizeof(v));}
static uint64_t m_fnv_i64(uint64_t h,int64_t v){return m_fnv_bytes(h,&v,sizeof(v));}
static double m_clamp(double v,double lo,double hi){return v<lo?lo:(v>hi?hi:v);}
static double m_wrap(double a){while(a>M_PI)a-=2*M_PI;while(a<-M_PI)a+=2*M_PI;return a;}

uint64_t facility_state_hash(const Facility *f){
    uint64_t h=FNV_OFFSET; h=m_fnv_u64(h,f->seed); h=m_fnv_i64(h,f->tick); h=m_fnv_i64(h,f->phase); h=m_fnv_i64(h,f->failure); h=m_fnv_i64(h,(int64_t)llround(f->player_x*1000000)); h=m_fnv_i64(h,(int64_t)llround(f->player_y*1000000)); h=m_fnv_i64(h,(int64_t)llround(f->player_angle*1000000)); h=m_fnv_i64(h,f->watcher_successes); h=m_fnv_i64(h,f->track_successes); h=m_fnv_i64(h,f->assembly_placed); h=m_fnv_u64(h,f->event_hash); h=m_fnv_u64(h,f->input_hash); for(int y=0;y<f->map_h;y++)h=m_fnv_bytes(h,f->map[y],f->map_w); return h;
}

const char *facility_failure_name(FailureReason r){ switch(r){case FAIL_NONE:return"none";case FAIL_EPISODE_DEADLINE:return"episode_deadline";case FAIL_WATCHER_DEADLINE:return"watcher_deadline";case FAIL_TRACK_DEADLINE:return"track_deadline";case FAIL_PREMATURE_ACTION:return"premature_action";case FAIL_STALE_ACTION:return"stale_action";case FAIL_WRONG_TARGET:return"wrong_target";case FAIL_TYPING_ERROR:return"typing_error";case FAIL_ASSEMBLY_MISS:return"assembly_miss";}return"unknown"; }
const char *facility_phase_name(FacilityPhase p){ switch(p){case PHASE_NAV:return"nav";case PHASE_TERMINAL:return"terminal";case PHASE_ASSEMBLY:return"assembly";case PHASE_DONE:return"done";case PHASE_FAILED:return"failed";}return"unknown"; }

void reference_init(ReferenceController *r){ memset(r,0,sizeof(*r)); r->path_index=1; }

static void reference_common(Facility *f, FacilityInput *in){
    for(int i=0;i<f->d.watcher_count;i++) if(f->watchers[i].active){ in->ack_index=i; break; }
    if(f->phase==PHASE_NAV && f->track_active){
        TrackObject *o=&f->track[f->track_authoritative]; int ox=FACILITY_W-174,oy=FACILITY_H-114; in->mouse_pressed=1; in->mouse_x=(int)llround(ox+o->x); in->mouse_y=(int)llround(oy+o->y);
    }
}

void reference_next(Facility *f, ReferenceController *r, FacilityInput *in){
    facility_input_clear(in); reference_common(f,in);
    if(f->phase==PHASE_NAV){
        if(r->path_index>=f->path_len) return;
        double tx=f->path_x[r->path_index]+0.5,ty=f->path_y[r->path_index]+0.5; double dx=tx-f->player_x,dy=ty-f->player_y; if(hypot(dx,dy)<0.18 && r->path_index<f->path_len-1){r->path_index++;tx=f->path_x[r->path_index]+0.5;ty=f->path_y[r->path_index]+0.5;dx=tx-f->player_x;dy=ty-f->player_y;}
        double desired=atan2(dy,dx),diff=m_wrap(desired-f->player_angle); in->turn_delta=m_clamp(diff,-0.18,0.18); if(fabs(diff)<0.38)in->forward=1;
    }else if(f->phase==PHASE_TERMINAL){
        if(r->typing_index<(int)strlen(f->code)){ in->typed_char=f->code[r->typing_index++]; }
        else in->enter=1;
    }else if(f->phase==PHASE_ASSEMBLY){
        while(r->assembly_index<f->piece_count && f->pieces[r->assembly_index].placed) r->assembly_index++;
        if(r->assembly_index>=f->piece_count) return;
        AssemblyPiece *p=&f->pieces[r->assembly_index];
        if(r->drag_state==0){ in->mouse_pressed=1;in->mouse_down=1;in->mouse_x=(int)p->x;in->mouse_y=(int)p->y;r->drag_state=1; }
        else if(r->drag_state==1){ in->mouse_down=1;in->mouse_x=(int)p->slot_x;in->mouse_y=(int)p->slot_y;r->drag_state=2; }
        else { in->mouse_released=1;in->mouse_x=(int)p->slot_x;in->mouse_y=(int)p->slot_y;r->drag_state=0;r->assembly_index++; }
    }
}

static void json_escape(FILE *fp,const char *s){ for(;*s;s++){ if(*s=='"'||*s=='\\')fputc('\\',fp); fputc(*s,fp);} }
int facility_write_report(const Facility *f,const char *path,double wall_seconds,uint64_t state_hash){
    FILE *fp=path?fopen(path,"w"):stdout; if(!fp)return-1;
    fprintf(fp,"{\n"); fprintf(fp,"  \"schema\": \"procedural-ops-facility-report-v0\",\n"); fprintf(fp,"  \"seed\": %llu,\n",(unsigned long long)f->seed); fprintf(fp,"  \"success\": %s,\n",f->success?"true":"false"); fprintf(fp,"  \"phase\": \"");json_escape(fp,facility_phase_name(f->phase));fprintf(fp,"\",\n"); fprintf(fp,"  \"failure\": \"");json_escape(fp,facility_failure_name(f->failure));fprintf(fp,"\",\n"); fprintf(fp,"  \"ticks\": %d,\n",f->tick); fprintf(fp,"  \"sim_seconds\": %.6f,\n",f->tick/60.0); fprintf(fp,"  \"wall_seconds\": %.9f,\n",wall_seconds); fprintf(fp,"  \"state_hash\": \"%016llx\",\n",(unsigned long long)state_hash); fprintf(fp,"  \"event_hash\": \"%016llx\",\n",(unsigned long long)f->event_hash); fprintf(fp,"  \"input_hash\": \"%016llx\",\n",(unsigned long long)f->input_hash); fprintf(fp,"  \"frame_hash\": \"%016llx\",\n",(unsigned long long)f->frame_hash);
    fprintf(fp,"  \"difficulty\": {\n    \"level\": %.6f, \"map_size\": %d, \"watcher_count\": %d, \"watcher_event_rate_hz\": %.6f, \"watcher_deadline_ticks\": %d,\n    \"track_distractors\": %d, \"track_speed_px_per_tick\": %.6f, \"track_target_radius_px\": %.6f, \"track_event_interval_ticks\": %d, \"track_deadline_ticks\": %d,\n    \"code_length\": %d, \"assembly_pieces\": %d, \"assembly_tolerance_px\": %.6f, \"recovery_displacement_px\": %.6f, \"episode_deadline_ticks\": %d, \"fov_deg\": %.6f\n  },\n",f->d.level,f->d.map_size,f->d.watcher_count,f->d.watcher_event_rate_hz,f->d.watcher_deadline_ticks,f->d.track_distractors,f->d.track_speed_px_per_tick,f->d.track_target_radius_px,f->d.track_event_interval_ticks,f->d.track_deadline_ticks,f->d.code_length,f->d.assembly_pieces,f->d.assembly_tolerance_px,f->d.recovery_displacement_px,f->d.episode_deadline_ticks,f->d.fov_deg);
    fprintf(fp,"  \"metrics\": {\n    \"watcher_events\": %d, \"watcher_successes\": %d, \"watcher_deadline_misses\": %d,\n    \"track_events\": %d, \"track_successes\": %d, \"wrong_targets\": %d,\n    \"premature_actions\": %d, \"stale_actions\": %d, \"assembly_placed\": %d, \"assembly_misses\": %d,\n    \"recovery_events\": %d, \"recovery_successes\": %d\n  }\n",f->watcher_events,f->watcher_successes,f->watcher_deadline_misses,f->track_events,f->track_successes,f->wrong_targets,f->premature_actions,f->stale_actions,f->assembly_placed,f->assembly_misses,f->recovery_events,f->recovery_successes); fprintf(fp,"}\n"); if(path)fclose(fp); return 0;
}

int facility_write_ppm(const uint32_t *pixels,int w,int h,const char *path){ FILE *fp=fopen(path,"wb");if(!fp)return-1;fprintf(fp,"P6\n%d %d\n255\n",w,h);for(int i=0;i<w*h;i++){unsigned char rgbv[3]={(pixels[i]>>16)&255,(pixels[i]>>8)&255,pixels[i]&255};fwrite(rgbv,1,3,fp);}fclose(fp);return 0; }
