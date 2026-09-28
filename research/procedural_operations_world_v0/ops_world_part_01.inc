static int generate_alert_schedule(OwWorld *w) {
    w->alert_schedule_count = 0;
    w->alert_schedule_cursor = 0;
    for (int i=0;i<w->watcher_count;++i) {
        w->watchers[i].next_event = 1e30;
        w->watchers[i].deadline = 0.0;
        w->watchers[i].ack_flash_until = 0.0;
        w->watchers[i].generation = 0;
        w->watchers[i].alert = 0;
        w->watchers[i].acknowledged = 0;
    }
    if (w->d.required_alerts <= 0) return 0;

    double available[OW_MAX_WATCHERS];
    for (int i=0;i<w->watcher_count;++i) available[i] = 0.0;
    int remaining = w->d.required_alerts;
    double t = 0.35;
    int burst_no = 0;
    while (remaining > 0) {
        int burst = w->d.alert_burst < remaining ? w->d.alert_burst : remaining;
        double interval = ((double)burst / (double)w->d.event_rate) * (0.82 + 0.36 * (double)rng_f01(w));
        t += interval;

        double free_times[OW_MAX_WATCHERS];
        for (int i=0;i<w->watcher_count;++i) free_times[i] = available[i];
        qsort(free_times, (size_t)w->watcher_count, sizeof(double), compare_double);
        if (burst > 0 && free_times[burst-1] > t) t = free_times[burst-1];

        if (t + w->d.alert_deadline >= w->d.episode_seconds) return -1;
        int chosen[OW_MAX_WATCHERS];
        int n = 0;
        for (int i=0;i<w->watcher_count;++i) if (available[i] <= t + 1e-9) chosen[n++] = i;
        if (n < burst) return -1;
        for (int i=n-1;i>0;--i) { int j=rng_int(w,0,i+1), q=chosen[i]; chosen[i]=chosen[j]; chosen[j]=q; }
        for (int k=0;k<burst;++k) {
            if (w->alert_schedule_count >= OW_MAX_ALERT_SCHEDULE) return -1;
            int idx = chosen[k];
            OwScheduledAlert *e = &w->alert_schedule[w->alert_schedule_count++];
            e->t = t;
            e->watcher = (uint8_t)idx;
            e->burst_slot = (uint8_t)k;
            available[idx] = t + w->d.alert_deadline + 1e-6;
            if (w->watchers[idx].next_event > t) w->watchers[idx].next_event = t;
        }
        remaining -= burst;
        ++burst_no;
        if (burst_no > OW_MAX_ALERT_SCHEDULE) return -1;
    }
    return w->alert_schedule_count == w->d.required_alerts ? 0 : -1;
}

static void generate_code(OwWorld *w) {
    static const char alphabet[] = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    int n = w->d.typing_length;
    for (int i = 0; i < n; ++i) w->source_code[i] = alphabet[rng_int(w, 0, (int)strlen(alphabet))];
    w->source_code[n] = 0;
}

static void init_task_graph(OwWorld *w) {
    uint8_t tasks[3] = {OW_TASK_TRANSFER, OW_TASK_ASSEMBLY, OW_TASK_TARGET};
    for (int i=2;i>0;--i) { int j=rng_int(w,0,i+1); uint8_t q=tasks[i]; tasks[i]=tasks[j]; tasks[j]=q; }
    w->task_mask = 0;
    memset(w->task_order, 0, sizeof(w->task_order));
    memset(w->task_deps, 0, sizeof(w->task_deps));
    for (int i=0;i<w->d.work_task_count;++i) {
        w->task_order[i] = tasks[i];
        w->task_mask |= tasks[i];
    }
    if (w->d.required_alerts > 0) w->task_mask |= OW_TASK_ALERTS;
    int links = w->d.dependency_depth;
    if (links > w->d.work_task_count - 1) links = w->d.work_task_count - 1;
    for (int i=1;i<=links;++i) {
        int idx = task_index(w->task_order[i]);
        if (idx >= 0) w->task_deps[idx] = w->task_order[i-1];
    }
    w->task_graph_variant = (uint8_t)(((w->task_order[0]&7u) << 4) ^ ((w->task_order[1]&7u) << 1) ^ (uint8_t)links);
    if (!task_required(w, OW_TASK_TRANSFER)) w->terminal_complete = 1;
    if (!task_required(w, OW_TASK_ASSEMBLY)) w->assembly_complete = 1;
    if (!task_required(w, OW_TASK_TARGET)) w->target_complete = 1;
}

static uint8_t station_task_bit(uint8_t kind) {
    if (kind == OW_STATION_SOURCE || kind == OW_STATION_TERMINAL) return OW_TASK_TRANSFER;
    if (kind == OW_STATION_ASSEMBLY) return OW_TASK_ASSEMBLY;
    if (kind == OW_STATION_MONITOR) return OW_TASK_ALERTS;
    return 0;
}

static void init_stations(OwWorld *w, int cells[][2], int n) {
    uint8_t kinds[4];
    int kcount = 0;
    if (task_required(w, OW_TASK_TRANSFER)) { kinds[kcount++] = OW_STATION_SOURCE; kinds[kcount++] = OW_STATION_TERMINAL; }
    if (task_required(w, OW_TASK_ASSEMBLY)) kinds[kcount++] = OW_STATION_ASSEMBLY;
    if (task_required(w, OW_TASK_ALERTS)) kinds[kcount++] = OW_STATION_MONITOR;
    w->station_count = kcount;
    int palette[6] = {0,1,2,3,4,5};
    for (int i=5;i>0;--i) { int j=rng_int(w,0,i+1), q=palette[i]; palette[i]=palette[j]; palette[j]=q; }
    int used = 0;
    for (int s = 0; s < kcount; ++s) {
        int found = 0;
        for (; used < n; ++used) {
            float x = cells[used][0] + 0.5f, y = cells[used][1] + 0.5f;
            if (hypotf(x - w->px, y - w->py) < 3.0f) continue;
            int good = 1;
            for (int j = 0; j < s; ++j)
                if (hypotf(x - w->stations[j].x, y - w->stations[j].y) < 4.0f) good = 0;
            if (!good) continue;
            w->stations[s].x = x;
            w->stations[s].y = y;
            w->stations[s].kind = kinds[s];
            w->stations[s].color = (uint8_t)palette[s % 6];
            w->stations[s].icon_style = (uint8_t)((w->presentation_family + s) % 3);
            ++used;
            found = 1;
            break;
        }
        if (!found) { w->done=1; w->failure_code=OW_FAIL_EPISODE_GENERATION; return; }
    }
}

static void init_objects(OwWorld *w, int cells[][2], int n) {
    w->object_count = w->d.object_count;
    w->target_object = rng_int(w, 0, w->object_count);
    uint8_t target_color = (uint8_t)rng_int(w, 0, 6);
    uint8_t target_shape = (uint8_t)rng_int(w, 0, 4);
    for (int i = 0; i < w->object_count; ++i) {
        int idx = rng_int(w, 0, n);
        OwObject *o = &w->objects[i];
        o->x = cells[idx][0] + rng_range(w, 0.25f, 0.75f);
        o->y = cells[idx][1] + rng_range(w, 0.25f, 0.75f);
        float a = rng_range(w, 0.0f, (float)(2*M_PI));
        float sp = w->d.target_speed * rng_range(w, 0.55f, 1.0f);
        o->vx = cosf(a) * sp;
        o->vy = sinf(a) * sp;
        if (i == w->target_object) {
            o->color = target_color; o->shape = target_shape; o->target = 1;
        } else {
            do {
                o->color = (uint8_t)rng_int(w, 0, 6);
                o->shape = (uint8_t)rng_int(w, 0, 4);
            } while (o->color == target_color && o->shape == target_shape);
            o->target = 0;
        }
        o->active = 1;
    }
    w->target_hits_required = 2;
    OwObject *t = &w->objects[w->target_object];
    w->target_reloc_x = t->x; w->target_reloc_y = t->y;
    for (int tries=0; tries<256; ++tries) {
        int idx = rng_int(w,0,n);
        float nx = cells[idx][0] + rng_range(w,0.25f,0.75f);
        float ny = cells[idx][1] + rng_range(w,0.25f,0.75f);
        if (!wall_at(w,nx,ny) && hypotf(nx-t->x,ny-t->y) > 5.0f) {
            w->target_reloc_x = nx; w->target_reloc_y = ny; break;
        }
    }
}

static void shuffle_ints(OwWorld *w, int *v, int n) {
    for (int i=n-1;i>0;--i) { int j=rng_int(w,0,i+1), t=v[i]; v[i]=v[j]; v[j]=t; }
}

static void init_assembly(OwWorld *w) {
    w->piece_count = w->d.assembly_pieces;
    int left[OW_MAX_ASSEMBLY], right[OW_MAX_ASSEMBLY], sem[24];
    for (int i=0;i<OW_MAX_ASSEMBLY;++i) left[i]=right[i]=i;
    for (int i=0;i<24;++i) sem[i]=i;
    shuffle_ints(w,left,OW_MAX_ASSEMBLY);
    shuffle_ints(w,right,OW_MAX_ASSEMBLY);
    shuffle_ints(w,sem,24);
    for (int i = 0; i < w->piece_count; ++i) {
        OwPiece *p = &w->pieces[i];
        int li=left[i], ri=right[i];
        int lc=li%3, lr=li/3, rc=ri%3, rr=ri/3;
        p->x = OW_PANEL_X + 45.0f + lc * 55.0f;
        p->y = OW_PANEL_Y + 40.0f + lr * 52.0f;
        p->home_x = p->x; p->home_y = p->y;
        p->slot_x = OW_PANEL_X + OW_PANEL_W/2.0f + 45.0f + rc * 55.0f;
        p->slot_y = OW_PANEL_Y + 40.0f + rr * 52.0f;
        p->color = (uint8_t)(sem[i] / 4);
        p->shape = (uint8_t)(sem[i] % 4);
        p->placed = 0;
    }
    w->drag_piece = -1;
}

void ow_init_with_family(OwWorld *w, uint64_t seed, uint64_t family_key, const OwDifficulty *d) {
    memset(w, 0, sizeof(*w));
    w->seed = seed;
    w->family_key = family_key;
    w->d = *d;
    uint64_t fm = family_key ^ 0x8cb92ba72f3d8dd7ULL;
    uint64_t family_mix = splitmix64(&fm);
    w->rng_state = seed ^ family_mix ^ 0xd1b54a32d192ed03ULL;
    uint64_t pv = family_mix ^ seed ^ 0x94d049bb133111ebULL;
    w->presentation_family = (uint8_t)(splitmix64(&pv) % 12u);
    w->started_wall = mono_time();
    init_map(w);
    int cells[OW_MAP_W * OW_MAP_H][2];
    int n = 0;
    collect_free_cells(w, cells, &n);
    shuffle_cells(w, cells, n);
    if (n < 8) { w->done=1; w->failure_code=OW_FAIL_EPISODE_GENERATION; return; }
    w->px = cells[0][0] + 0.5f;
    w->py = cells[0][1] + 0.5f;
    w->angle = rng_range(w, (float)-M_PI, (float)M_PI);
    w->cursor_x = OW_WIDTH/2.0f;
    w->cursor_y = OW_HUD_H/2.0f;
    init_task_graph(w);
    init_stations(w, cells, n);
    if (w->done) return;
    init_objects(w, cells, n);
    if (task_required(w, OW_TASK_ASSEMBLY)) init_assembly(w); else { w->piece_count=0; w->drag_piece=-1; }
    if (task_required(w, OW_TASK_TRANSFER)) generate_code(w); else { w->source_code[0]=0; w->typed_code[0]=0; }
    w->watcher_count = w->d.watcher_count;
    if (generate_alert_schedule(w)) {
        w->done=1; w->success=0; w->failure_code=OW_FAIL_EPISODE_GENERATION;
        log_event(w, EV_EPISODE_GENERATION, 1, 0, 0, 0);
        return;
    }
    w->active_station = -1;
    w->drag_piece = -1;
    w->episode_hash = ow_state_hash(w);
}

void ow_init(OwWorld *w, uint64_t seed, const OwDifficulty *d) {
    ow_init_with_family(w, seed, 0, d);
}

static void move_player(OwWorld *w, double dt) {
    float fwd = (w->key_w ? 1.0f : 0.0f) - (w->key_s ? 1.0f : 0.0f);
    float str = (w->key_d ? 1.0f : 0.0f) - (w->key_a ? 1.0f : 0.0f);
    if (fwd == 0.0f && str == 0.0f) return;
    float n = sqrtf(fwd*fwd + str*str);
    fwd /= n; str /= n;
    float ca = cosf(w->angle), sa = sinf(w->angle);
    float dx = (ca*fwd - sa*str) * w->d.navigation_speed * (float)dt;
    float dy = (sa*fwd + ca*str) * w->d.navigation_speed * (float)dt;
    float nx = w->px + dx, ny = w->py + dy;
    if (!wall_at(w, nx, w->py)) w->px = nx;
    if (!wall_at(w, w->px, ny)) w->py = ny;
}

static void move_objects(OwWorld *w, double dt) {
    for (int i = 0; i < w->object_count; ++i) {
        OwObject *o = &w->objects[i];
        float nx = o->x + o->vx * (float)dt;
        float ny = o->y + o->vy * (float)dt;
        if (wall_at(w, nx, o->y)) { o->vx = -o->vx; nx = o->x + o->vx*(float)dt; }
        if (wall_at(w, o->x, ny)) { o->vy = -o->vy; ny = o->y + o->vy*(float)dt; }
        o->x = nx; o->y = ny;
    }
}

static void trigger_alert(OwWorld *w, int idx, double scheduled_t) {
    OwWatcher *q = &w->watchers[idx];
    if (q->alert) {
        w->done=1; w->success=0; w->failure_code=OW_FAIL_EPISODE_GENERATION;
        log_event(w, EV_EPISODE_GENERATION, 2, idx, 0, 0);
        return;
    }
    q->alert = 1;
    q->acknowledged = 0;
    q->generation++;
    q->deadline = scheduled_t + w->d.alert_deadline;
    ++w->alerts_spawned;
    log_event(w, EV_ALERT_ON, idx, (int)q->generation, 0, 0);
}

static void update_watchers(OwWorld *w) {
    while (!w->done && w->alert_schedule_cursor < w->alert_schedule_count &&
           w->alert_schedule[w->alert_schedule_cursor].t <= w->sim_time + 1e-12) {
        const OwScheduledAlert *se = &w->alert_schedule[w->alert_schedule_cursor];
        int idx = se->watcher;
        trigger_alert(w, idx, se->t);
        ++w->alert_schedule_cursor;
    }
    for (int i = 0; i < w->watcher_count && !w->done; ++i) {
        OwWatcher *q = &w->watchers[i];
        if (q->alert && w->sim_time > q->deadline) {
            q->alert = 0;
            q->acknowledged = 0;
            ++w->alerts_missed;
            log_event(w, EV_ALERT_MISS, i, (int)q->generation, 0, 0);
            if (w->failure_code != OW_FAIL_EVENT_OVERFLOW) {
                w->done = 1; w->success = 0; w->failure_code = OW_FAIL_MISSED_ALERT;
            }
            return;
        }
        if (q->acknowledged && w->sim_time >= q->ack_flash_until) q->acknowledged = 0;
    }
}

static void maybe_finish(OwWorld *w) {
    if (w->done) return;
    int transfer_ok = !task_required(w,OW_TASK_TRANSFER) || w->terminal_complete;
    int assembly_ok = !task_required(w,OW_TASK_ASSEMBLY) || w->assembly_complete;
    int target_ok = !task_required(w,OW_TASK_TARGET) || w->target_complete;
    int alerts_ok = !task_required(w,OW_TASK_ALERTS) || w->alerts_acked >= w->d.required_alerts;
    if (transfer_ok && assembly_ok && target_ok && alerts_ok) {
        w->done = 1;
        w->success = 1;
        w->failure_code = OW_FAIL_NONE;
        log_event(w, EV_SUCCESS, 0, 0, 0, 0);
    } else if (w->sim_time >= w->d.episode_seconds) {
        w->done = 1;
        w->success = 0;
        w->failure_code = OW_FAIL_EPISODE_TIMEOUT;
        log_event(w, EV_TIMEOUT, 0, 0, 0, 0);
    }
}
