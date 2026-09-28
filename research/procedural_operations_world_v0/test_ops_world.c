#include "ops_world.h"
#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void disable_alerts(OwDifficulty *d){d->required_alerts=0;d->event_rate=0;}
static void watcher_xy(const OwWorld *w,int idx,float*x,float*y){
    int n=w->watcher_count;int m=w->presentation_family%4,slot=-1;
    for(int s=0;s<n;++s){int mults[6]={1,5,7,11,13,17};int mm=mults[w->presentation_family%6];while(mm<n&&({int a=mm,b=n;while(b){int t=a%b;a=b;b=t;}a;})!=1)mm+=2;int off=(w->presentation_family*7u)%(unsigned)n;int ch=(s*mm+off)%n;if(ch==idx){slot=s;break;}}
    if(slot<0){*x=*y=0;return;}int tw=22,th=16;
    if(m==0){int cols=32;*x=8+(slot%cols)*19+9;*y=6+(slot/cols)*19+8;}
    else if(m==1){int per=(n+1)/2;if(slot<per){*x=6+(slot%2)*19+9;*y=OW_HUD_H+8+(slot/2)*19+8;}else{int k=slot-per;*x=OW_WIDTH-44+(k%2)*19+9;*y=OW_HUD_H+8+(k/2)*19+8;}}
    else if(m==2){int per=(n+3)/4,corner=slot/per,k=slot%per;int col=k%4,row=k/4;int bx=(corner==1||corner==3)?OW_WIDTH-4*19-10:8;int by=(corner>=2)?OW_HEIGHT-((per+3)/4)*19-8:6;*x=bx+col*19+9;*y=by+row*19+8;}
    else{int per=(n+1)/2;if(slot<per){*x=8+(slot%32)*19+9;*y=6+(slot/32)*19+8;}else{int k=slot-per;*x=8+(k%32)*19+9;*y=OW_HEIGHT-22-(k/32)*19+8;}}
    (void)tw;(void)th;
}
static int find_station(const OwWorld*w,int kind){for(int i=0;i<w->station_count;++i)if(w->stations[i].kind==kind)return i;return -1;}
static void empty_room(OwWorld*w){for(int y=0;y<OW_MAP_H;++y)for(int x=0;x<OW_MAP_W;++x)w->map[y][x]=(x==0||y==0||x==OW_MAP_W-1||y==OW_MAP_H-1)?1:0;w->px=5.5f;w->py=5.5f;w->angle=0;}

static void test_params_and_feasibility(void) {
    OwDifficulty d; ow_default_difficulty(&d); char err[128];
    assert(ow_set_param(&d,"object_count",64,err,sizeof(err))==0); assert(d.object_count==64);
    assert(ow_set_param(&d,"no_such",1,err,sizeof(err))!=0);
    OwDifficulty bad=d; bad.required_alerts=8; bad.event_rate=0; assert(ow_validate_difficulty(&bad,err,sizeof(err))!=0);
    bad=d; bad.watcher_count=2; bad.required_alerts=8; bad.event_rate=50; bad.alert_deadline=1; assert(ow_validate_difficulty(&bad,err,sizeof(err))!=0);
    OwDifficulty boundary;ow_default_difficulty(&boundary);boundary.required_alerts=8;boundary.event_rate=0.161f;boundary.alert_burst=1;boundary.episode_seconds=75;boundary.alert_deadline=2.5f;assert(ow_validate_difficulty(&boundary,err,sizeof(err))==0);
    for(uint64_t seed=0;seed<10000;++seed){OwWorld w;ow_init_with_family(&w,seed,999,&boundary);assert(w.failure_code!=OW_FAIL_EPISODE_GENERATION);assert(w.alert_schedule_count==8);assert(w.alert_schedule[7].t+boundary.alert_deadline<boundary.episode_seconds);}
}

static void test_determinism_and_private_family(void) {
    OwDifficulty d;ow_default_difficulty(&d);OwWorld a,b,c;ow_init_with_family(&a,12345,11,&d);ow_init_with_family(&b,12345,11,&d);ow_init_with_family(&c,12345,12,&d);
    assert(a.episode_hash==b.episode_hash);assert(ow_state_hash(&a)==ow_state_hash(&b));assert(a.episode_hash!=c.episode_hash);
    for(int i=0;i<300&&!a.done&&!b.done;++i){ow_step(&a,1.0/60.0);ow_step(&b,1.0/60.0);}assert(ow_state_hash(&a)==ow_state_hash(&b));
}

static void test_task_graph_and_generation_variation(void) {
    OwDifficulty d;ow_default_difficulty(&d);disable_alerts(&d);d.work_task_count=2;d.dependency_depth=1;
    unsigned masks=0,present=0,maps=0;for(uint64_t seed=0;seed<400;++seed){OwWorld w;ow_init_with_family(&w,seed,seed*31+7,&d);masks|=1u<<w.task_mask;present|=1u<<(w.presentation_family%12);maps|=1u<<(w.map_variant%8);int count=0;for(int b=1;b<=4;b<<=1)if(w.task_mask&b)count++;assert(count==2);}assert(__builtin_popcount(masks)>=3);assert((present&0xfff)==0xfff);assert((maps&0xff)==0xff);
}

static void test_target_semantic_uniqueness(void) {
    OwDifficulty d;ow_default_difficulty(&d);disable_alerts(&d);d.object_count=64;
    for(uint64_t seed=0;seed<10000;++seed){OwWorld w;ow_init_with_family(&w,seed,1234,&d);OwObject*t=&w.objects[w.target_object];int matches=0;for(int i=0;i<w.object_count;++i)if(w.objects[i].color==t->color&&w.objects[i].shape==t->shape)matches++;assert(matches==1);}
}

static void test_schedule_exact_feasible_and_rate_independent_of_burst(void) {
    double avg_last[2]={0};int bursts[2]={1,8};
    for(int bi=0;bi<2;++bi){OwDifficulty d;ow_default_difficulty(&d);d.watcher_count=64;d.required_alerts=80;d.event_rate=8;d.alert_deadline=1.0f;d.alert_burst=bursts[bi];d.episode_seconds=40;char err[128];assert(ow_validate_difficulty(&d,err,sizeof(err))==0);
        for(uint64_t s=0;s<100;++s){OwWorld w;ow_init_with_family(&w,s,90,&d);assert(w.alert_schedule_count==80);double last=w.alert_schedule[79].t; assert(last+d.alert_deadline<d.episode_seconds); avg_last[bi]+=last;
        }
        avg_last[bi]/=100.0;
        double realized=80.0/(avg_last[bi]-0.35); assert(realized>6.3 && realized<9.8);
    }
    assert(fabs(avg_last[0]-avg_last[1]) < 2.0);
}

static void test_schedule_future_independent_of_ack_timing(void) {
    OwDifficulty d; ow_default_difficulty(&d); d.watcher_count=64; d.required_alerts=24; d.event_rate=6; d.alert_deadline=2; d.alert_burst=4; d.episode_seconds=60; d.dependency_depth=0;
    OwWorld a,b; ow_init_with_family(&a,909,12345,&d); ow_init_with_family(&b,909,12345,&d);
    assert(a.episode_hash==b.episode_hash); assert(a.alert_schedule_count==b.alert_schedule_count);
    assert(memcmp(a.alert_schedule,b.alert_schedule,sizeof(OwScheduledAlert)*(size_t)a.alert_schedule_count)==0);
    double t=a.alert_schedule[0].t+0.05; ow_step(&a,t); ow_step(&b,t);
    int idx=-1;for(int i=0;i<a.watcher_count;++i)if(a.watchers[i].alert){idx=i;break;}assert(idx>=0);
    float x,y;watcher_xy(&a,idx,&x,&y);ow_mouse_button(&a,1,1,x,y);
    ow_step(&a,0.5); ow_step(&b,0.5); watcher_xy(&b,idx,&x,&y);ow_mouse_button(&b,1,1,x,y);
    assert(memcmp(a.alert_schedule,b.alert_schedule,sizeof(OwScheduledAlert)*(size_t)a.alert_schedule_count)==0);
    assert(a.alert_schedule_cursor==b.alert_schedule_cursor);
    for(int i=0;i<a.watcher_count;++i) assert(fabs(a.watchers[i].next_event-b.watchers[i].next_event)<1e-12);
}

static void test_high_concurrency_generation(void) {
    OwDifficulty d; ow_default_difficulty(&d); d.watcher_count=64; d.object_count=64; d.event_rate=20; d.alert_deadline=2; d.alert_burst=16; d.required_alerts=64; d.episode_seconds=60;
    char err[128]; assert(ow_validate_difficulty(&d,err,sizeof(err))==0);
    OwWorld w; ow_init_with_family(&w,99,222,&d); assert(w.alert_schedule_count==64);
    double first=w.alert_schedule[0].t; ow_step(&w,first+0.01); int active=0;for(int i=0;i<w.watcher_count;++i)active+=w.watchers[i].alert?1:0;
    assert(w.watcher_count==64&&w.object_count==64&&active==16);
}

static void test_typing_recovery(void) {
    OwDifficulty d; ow_default_difficulty(&d); disable_alerts(&d); d.dependency_depth=0; d.recovery_budget=2;
    OwWorld w; ow_init(&w,7,&d); int term=find_station(&w,OW_STATION_TERMINAL); assert(term>=0); w.panel_open=1; w.active_station=term;
    ow_text(&w,'0');ow_enter(&w);assert(!w.done&&!w.terminal_complete&&w.recoverable_errors==1&&w.typed_len==0);
    for(const char*p=w.source_code;*p;++p) ow_text(&w,*p);
    ow_enter(&w);
    assert(w.terminal_complete&&w.recoveries==1);
}

static void test_assembly_recovery(void) {
    OwDifficulty d; ow_default_difficulty(&d); disable_alerts(&d); d.dependency_depth=0; d.recovery_budget=2;
    OwWorld w; ow_init(&w,8,&d); int st=find_station(&w,OW_STATION_ASSEMBLY); assert(st>=0); w.panel_open=1; w.active_station=st;
    OwPiece *p=&w.pieces[0];float hx=p->home_x,hy=p->home_y;ow_mouse_button(&w,1,1,p->x,p->y);ow_mouse_move(&w,0,0,90,90);ow_mouse_button(&w,1,0,90,90);
    assert(!w.done&&w.recoverable_errors==1&&fabsf(p->x-hx)<0.01f&&fabsf(p->y-hy)<0.01f);
    for(int i=0;i<w.piece_count;++i){p=&w.pieces[i];ow_mouse_button(&w,1,1,p->x,p->y);ow_mouse_move(&w,0,0,p->slot_x,p->slot_y);ow_mouse_button(&w,1,0,p->slot_x,p->slot_y);}assert(w.assembly_complete&&w.recoveries>=1);
}

static void test_alert_ack_miss_and_false_ack(void) {
    OwDifficulty d; ow_default_difficulty(&d); d.required_alerts=1; d.event_rate=10; d.alert_deadline=0.2f; d.alert_burst=1; d.episode_seconds=10; d.dependency_depth=0;
    OwWorld w; ow_init_with_family(&w,11,333,&d);ow_step(&w,w.alert_schedule[0].t+0.01);int idx=-1;for(int i=0;i<w.watcher_count;++i)if(w.watchers[i].alert){idx=i;break;}assert(idx>=0);float x,y;watcher_xy(&w,idx,&x,&y);ow_mouse_button(&w,1,1,x,y);assert(w.alerts_acked==1&&w.alerts_missed==0);
    OwWorld m; ow_init_with_family(&m,12,333,&d);ow_step(&m,m.alert_schedule[0].t+d.alert_deadline+0.05);assert(m.done&&m.failure_code==OW_FAIL_MISSED_ALERT);
    OwDifficulty s;ow_default_difficulty(&s);s.required_alerts=0;s.event_rate=0;s.watcher_count=64;OwWorld spam;ow_init_with_family(&spam,13,444,&s);watcher_xy(&spam,0,&x,&y);ow_mouse_button(&spam,1,1,x,y);assert(spam.done&&spam.failure_code==OW_FAIL_FORBIDDEN_ACTION&&spam.false_acks==1);
}

static void test_wrong_target_hard_motor_miss_recoverable(void) {
    OwDifficulty d;ow_default_difficulty(&d);disable_alerts(&d);d.dependency_depth=0;d.recovery_budget=2;
    OwWorld w;ow_init(&w,30,&d);empty_room(&w);int wrong=(w.target_object==0)?1:0;w.object_count=2;w.objects[w.target_object].x=12.5f;w.objects[w.target_object].y=12.5f;w.objects[wrong].x=6.5f;w.objects[wrong].y=5.5f;w.objects[wrong].active=1;
    ow_mouse_button(&w,1,1,OW_WIDTH/2,OW_HUD_H+(OW_HEIGHT-OW_HUD_H)/2);assert(w.done&&w.failure_code==OW_FAIL_FORBIDDEN_ACTION&&w.wrong_actions==1);
    OwWorld m;ow_init(&m,31,&d);empty_room(&m);for(int i=0;i<m.object_count;++i){m.objects[i].x=12.5f;m.objects[i].y=12.5f;}ow_mouse_button(&m,1,1,OW_WIDTH/2,OW_HUD_H+(OW_HEIGHT-OW_HUD_H)/2);assert(!m.done&&m.motor_misses==1&&m.recoverable_errors==1);
    d.recovery_budget=0;OwWorld z;ow_init(&z,31,&d);empty_room(&z);for(int i=0;i<z.object_count;++i){z.objects[i].x=12.5f;z.objects[i].y=12.5f;}ow_mouse_button(&z,1,1,320,OW_HUD_H+(OW_HEIGHT-OW_HUD_H)/2);assert(z.done&&z.failure_code==OW_FAIL_RECOVERY_EXHAUSTED);
}

static void test_target_relocation_precomputed(void) {
    OwDifficulty d;ow_default_difficulty(&d);disable_alerts(&d);d.dependency_depth=0;d.target_speed=0;
    OwWorld a,b;ow_init_with_family(&a,13,5,&d);ow_init_with_family(&b,13,5,&d);empty_room(&a);empty_room(&b);int t=a.target_object;
    a.objects[t].x=b.objects[t].x=6.5f;a.objects[t].y=b.objects[t].y=5.5f;a.objects[t].vx=b.objects[t].vx=0;a.objects[t].vy=b.objects[t].vy=0;
    ow_mouse_button(&a,1,1,320,OW_HUD_H+(OW_HEIGHT-OW_HUD_H)/2);ow_step(&b,1.0);ow_mouse_button(&b,1,1,320,OW_HUD_H+(OW_HEIGHT-OW_HUD_H)/2);
    assert(a.target_hits==1&&b.target_hits==1);assert(fabsf(a.objects[t].x-b.objects[t].x)<1e-6f&&fabsf(a.objects[t].y-b.objects[t].y)<1e-6f);assert(fabsf(a.objects[t].x-a.target_reloc_x)<1e-6f);
}

static void test_realtime_catchup_equivalence(void) {
    OwDifficulty d;ow_default_difficulty(&d);disable_alerts(&d);d.target_speed=0;
    OwWorld a,b;ow_init_with_family(&a,55,7,&d);ow_init_with_family(&b,55,7,&d);ow_step(&a,1.0);for(int i=0;i<120;++i)ow_step(&b,1.0/120.0);
    assert(fabs(a.sim_time-1.0)<1e-9&&fabs(b.sim_time-1.0)<1e-9);assert(ow_state_hash(&a)==ow_state_hash(&b));assert(a.internal_steps==120&&a.max_step_dt>=1.0);
}

static void test_large_event_ledger_no_silent_truncation(void) {
    OwDifficulty d;ow_default_difficulty(&d);d.watcher_count=64;d.object_count=64;d.event_rate=20;d.alert_deadline=1;d.alert_burst=16;d.required_alerts=200;d.episode_seconds=60;d.dependency_depth=0;
    char err[128];assert(ow_validate_difficulty(&d,err,sizeof(err))==0);OwWorld w;ow_init_with_family(&w,77,9,&d);
    for(int guard=0;guard<200000&&w.alerts_acked<d.required_alerts&&!w.done;++guard){ow_step(&w,0.001);for(int i=0;i<w.watcher_count&&!w.done;++i)if(w.watchers[i].alert){float x,y;watcher_xy(&w,i,&x,&y);ow_mouse_button(&w,1,1,x,y);}}
    assert(!w.event_overflow);assert(w.alerts_acked==200);assert(w.event_count>=400&&w.event_count<OW_MAX_EVENTS);
}

static void test_hidden_score_progress_not_rendered(void) {
    OwDifficulty d;ow_default_difficulty(&d);d.dependency_depth=0;OwWorld a;ow_init_with_family(&a,77,901,&d);OwWorld b=a;
    a.alerts_acked=0;b.alerts_acked=d.required_alerts-1;a.target_hits=0;b.target_hits=1;
    for(int i=0;i<a.watcher_count;++i){a.watchers[i].acknowledged=b.watchers[i].acknowledged=0;a.watchers[i].alert=b.watchers[i].alert=0;}
    OwFrame fa,fb;fa.pixels=calloc((size_t)OW_WIDTH*OW_HEIGHT,sizeof(uint32_t));fb.pixels=calloc((size_t)OW_WIDTH*OW_HEIGHT,sizeof(uint32_t));assert(fa.pixels&&fb.pixels);
    ow_render(&a,&fa);ow_render(&b,&fb);assert(memcmp(fa.pixels,fb.pixels,(size_t)OW_WIDTH*OW_HEIGHT*sizeof(uint32_t))==0);free(fa.pixels);free(fb.pixels);
}

static void test_render_cursor_and_presentation_variation(void) {
    OwDifficulty d;ow_default_difficulty(&d);d.watcher_count=64;OwFrame f;f.pixels=calloc((size_t)OW_WIDTH*OW_HEIGHT,sizeof(uint32_t));assert(f.pixels);uint64_t hashes[12]={0};int unique=0;
    for(uint64_t fk=0;fk<12;++fk){OwWorld w;ow_init_with_family(&w,2026,fk,&d);float x,y;watcher_xy(&w,0,&x,&y);w.cursor_x=x;w.cursor_y=y;ow_render(&w,&f);uint64_t h=1469598103934665603ULL;for(int i=0;i<OW_WIDTH*OW_HEIGHT;i+=97){h^=f.pixels[i];h*=1099511628211ULL;}int seen=0;for(int j=0;j<unique;++j)if(hashes[j]==h)seen=1;if(!seen)hashes[unique++]=h;}
    assert(unique>=6);free(f.pixels);
}

static void test_reset_hash(void) {
    OwDifficulty d;ow_default_difficulty(&d);OwWorld w;ow_init_with_family(&w,42,123,&d);uint64_t e=w.episode_hash,h=ow_state_hash(&w);for(int i=0;i<100&&!w.done;++i)ow_step(&w,1.0/60.0);ow_init_with_family(&w,42,123,&d);assert(e==w.episode_hash&&h==ow_state_hash(&w));
}

int main(void) {
    test_params_and_feasibility();
    test_determinism_and_private_family();
    test_task_graph_and_generation_variation();
    test_target_semantic_uniqueness();
    test_schedule_exact_feasible_and_rate_independent_of_burst();
    test_schedule_future_independent_of_ack_timing();
    test_high_concurrency_generation();
    test_typing_recovery();
    test_assembly_recovery();
    test_alert_ack_miss_and_false_ack();
    test_wrong_target_hard_motor_miss_recoverable();
    test_target_relocation_precomputed();
    test_realtime_catchup_equivalence();
    test_large_event_ledger_no_silent_truncation();
    test_hidden_score_progress_not_rendered();
    test_render_cursor_and_presentation_variation();
    test_reset_hash();
    puts("17/17 validity-hardening tests PASS");
    return 0;
}
