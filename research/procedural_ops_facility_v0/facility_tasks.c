#define _POSIX_C_SOURCE 200809L
#include "facility.h"
#include "facility_internal.h"
#include <math.h>
#include <string.h>

static void update_watchers(Facility *f, const FacilityInput *in) {
    for(int i=0;i<f->d.watcher_count;i++){
        Watcher *w=&f->watchers[i];
        if(!w->active && f->tick>=w->next_tick){
            w->active=1; w->generation++; w->deadline_tick=f->tick+f->d.watcher_deadline_ticks;
            f->watcher_events++; fac_hash_event(f,10,i,w->generation);
        }
        if(w->active && f->tick>w->deadline_tick){
            f->watcher_deadline_misses++; f->failure=FAIL_WATCHER_DEADLINE; f->phase=PHASE_FAILED; f->done=1; f->success=0;
            fac_hash_event(f,11,i,w->generation); return;
        }
    }
    if(in->ack_index>=0){
        int i=in->ack_index;
        if(i<0||i>=f->d.watcher_count){ f->premature_actions++; f->failure=FAIL_PREMATURE_ACTION; f->phase=PHASE_FAILED; f->done=1; return; }
        Watcher *w=&f->watchers[i];
        if(w->active){
            w->active=0; w->last_resolved_generation=w->generation; f->watcher_successes++; fac_schedule_watcher(f,i); fac_hash_event(f,12,i,w->generation);
        }else if(w->generation>0 && w->last_resolved_generation==w->generation){
            f->stale_actions++; f->failure=FAIL_STALE_ACTION; f->phase=PHASE_FAILED; f->done=1; fac_hash_event(f,13,i,w->generation);
        }else{
            f->premature_actions++; f->failure=FAIL_PREMATURE_ACTION; f->phase=PHASE_FAILED; f->done=1; fac_hash_event(f,14,i,w->generation);
        }
    }
}

static void move_track(Facility *f) {
    for(int i=0;i<f->track_count;i++){
        TrackObject *o=&f->track[i]; o->x+=o->vx; o->y+=o->vy;
        if(o->x<8){o->x=8+(8-o->x);o->vx=fabs(o->vx);} if(o->x>152){o->x=152-(o->x-152);o->vx=-fabs(o->vx);}
        if(o->y<8){o->y=8+(8-o->y);o->vy=fabs(o->vy);} if(o->y>92){o->y=92-(o->y-92);o->vy=-fabs(o->vy);}
    }
}

static void activate_track(Facility *f) {
    f->track_previous_authoritative=f->track_authoritative;
    if(f->track_count>1){ int n=f->track_authoritative; while(n==f->track_authoritative) n=fac_rng_int(f,f->track_count); f->track_authoritative=n; }
    f->track_active=1; f->track_generation++; f->track_deadline_tick=f->tick+f->d.track_deadline_ticks; f->track_events++;
    fac_hash_event(f,20,f->track_authoritative,f->track_generation);
}

static int point_in_track_obj(Facility *f, int sx, int sy, int i) {
    /* Feed coordinates are local 160x100 placed at right/bottom. */
    int ox=FACILITY_W-174, oy=FACILITY_H-114;
    double dx=sx-(ox+f->track[i].x), dy=sy-(oy+f->track[i].y);
    double r=f->d.track_target_radius_px;
    return dx*dx+dy*dy<=r*r;
}

static void update_track(Facility *f, const FacilityInput *in) {
    move_track(f);
    if(!f->track_active && f->tick>=f->track_next_event_tick) activate_track(f);
    if(f->track_active && f->tick>f->track_deadline_tick){
        f->failure=FAIL_TRACK_DEADLINE; f->phase=PHASE_FAILED; f->done=1; fac_hash_event(f,21,f->track_authoritative,f->track_generation); return;
    }
    if(in->mouse_pressed && f->phase==PHASE_NAV){
        int hit=-1;
        /* Overlapping moving objects can occur. A click that lies inside the authoritative object
           is accepted before considering overlapping distractors; otherwise classify stale/wrong. */
        if(point_in_track_obj(f,in->mouse_x,in->mouse_y,f->track_authoritative)) hit=f->track_authoritative;
        else if(f->track_previous_authoritative>=0 && point_in_track_obj(f,in->mouse_x,in->mouse_y,f->track_previous_authoritative)) hit=f->track_previous_authoritative;
        else {
            double best=1e30;
            int ox=FACILITY_W-174, oy=FACILITY_H-114;
            for(int i=0;i<f->track_count;i++) if(point_in_track_obj(f,in->mouse_x,in->mouse_y,i)){
                double dx=in->mouse_x-(ox+f->track[i].x), dy=in->mouse_y-(oy+f->track[i].y);
                double ds=dx*dx+dy*dy;
                if(ds<best){best=ds;hit=i;}
            }
        }
        if(!f->track_active){ f->premature_actions++; f->failure=FAIL_PREMATURE_ACTION; f->phase=PHASE_FAILED; f->done=1; fac_hash_event(f,22,hit,0); return; }
        if(hit==f->track_authoritative){
            f->track_active=0; f->track_successes++; f->track_next_event_tick=f->tick+f->d.track_event_interval_ticks; fac_hash_event(f,23,hit,f->track_generation);
        }else if(hit==f->track_previous_authoritative && hit>=0){
            f->stale_actions++; f->failure=FAIL_STALE_ACTION; f->phase=PHASE_FAILED; f->done=1; fac_hash_event(f,24,hit,f->track_generation);
        }else{
            f->wrong_targets++; f->failure=FAIL_WRONG_TARGET; f->phase=PHASE_FAILED; f->done=1; fac_hash_event(f,25,hit,f->track_generation);
        }
    }
}

static void enter_terminal(Facility *f){ f->phase=PHASE_TERMINAL; f->phase_tick=0; f->terminal_focus=1; fac_hash_event(f,30,0,0); }
static void enter_assembly(Facility *f){ f->phase=PHASE_ASSEMBLY; f->phase_tick=0; f->dragging_piece=-1; fac_hash_event(f,31,0,0); }

static int piece_at(Facility *f,int x,int y){
    for(int i=f->piece_count-1;i>=0;i--){ AssemblyPiece *p=&f->pieces[i]; if(p->placed)continue; if(hypot(x-p->x,y-p->y)<=18) return i; }
    return -1;
}

static void shift_recovery(Facility *f){
    if(f->recovery_triggered) return;
    f->recovery_triggered=1; f->recovery_events++;
    double shift=f->d.recovery_displacement_px;
    /* Translate all unresolved pieces through a wrapped left-pane coordinate.
       This forces reacquisition while preserving inter-piece separation. */
    double lo=36.0, hi=FACILITY_W/2.0-36.0, span=hi-lo;
    for(int i=0;i<f->piece_count;i++) if(!f->pieces[i].placed){
        double rel=f->pieces[i].x-lo;
        rel=fmod(rel+shift,span);
        if(rel<0) rel+=span;
        f->pieces[i].x=lo+rel;
    }
    fac_hash_event(f,40,(int)shift,0);
}

static void update_terminal(Facility *f, const FacilityInput *in){
    if(in->typed_char && f->typed_len<FACILITY_CODE_MAX){
        char c=(char)in->typed_char; if(c>='a'&&c<='z')c=(char)(c-'a'+'A'); f->typed[f->typed_len++]=c; f->typed[f->typed_len]='\0';
    }
    if(in->enter){
        if(!strcmp(f->typed,f->code)) enter_assembly(f);
        else { f->failure=FAIL_TYPING_ERROR; f->phase=PHASE_FAILED; f->done=1; fac_hash_event(f,32,f->typed_len,0); }
    }
}

static void update_assembly(Facility *f, const FacilityInput *in){
    if(in->mouse_pressed && f->dragging_piece<0) f->dragging_piece=piece_at(f,in->mouse_x,in->mouse_y);
    if(in->mouse_down && f->dragging_piece>=0){
        AssemblyPiece *p=&f->pieces[f->dragging_piece]; p->x=in->mouse_x; p->y=in->mouse_y;
    }
    if(in->mouse_released && f->dragging_piece>=0){
        int i=f->dragging_piece; AssemblyPiece *p=&f->pieces[i]; f->dragging_piece=-1;
        if(hypot(p->x-p->slot_x,p->y-p->slot_y)<=f->d.assembly_tolerance_px){
            p->x=p->slot_x; p->y=p->slot_y; p->placed=1; f->assembly_placed++; fac_hash_event(f,41,i,f->assembly_placed);
            if(f->assembly_placed==1) shift_recovery(f);
            if(f->assembly_placed>=f->piece_count){
                f->recovery_successes=f->recovery_triggered?1:0; f->phase=PHASE_DONE; f->done=1; f->success=1; fac_hash_event(f,42,f->assembly_placed,0);
            }
        }else{
            f->assembly_misses++; f->failure=FAIL_ASSEMBLY_MISS; f->phase=PHASE_FAILED; f->done=1; fac_hash_event(f,43,i,0);
        }
    }
}

void facility_step(Facility *f, const FacilityInput *in) {
    if(f->done) return;
    f->input_hash=fac_fnv_bytes(f->input_hash,in,sizeof(*in));
    f->tick++; f->phase_tick++;
    if(f->tick>f->d.episode_deadline_ticks){ f->failure=FAIL_EPISODE_DEADLINE; f->phase=PHASE_FAILED; f->done=1; return; }
    update_watchers(f,in); if(f->done)return;
    /* Tracking feed is deliberately concurrent with navigation only in v0. */
    if(f->phase==PHASE_NAV){ update_track(f,in); if(f->done)return; fac_apply_movement(f,in); }
    if(f->phase==PHASE_NAV){
        double tx=f->terminal_cx+0.5, ty=f->terminal_cy+0.5;
        if(hypot(f->player_x-tx,f->player_y-ty)<0.38) enter_terminal(f);
    }else if(f->phase==PHASE_TERMINAL){ update_terminal(f,in); }
    else if(f->phase==PHASE_ASSEMBLY){ update_assembly(f,in); }
}
