void ow_step(OwWorld *w, double dt) {
    if (w->done) return;
    if (dt < 0.0) dt = 0.0;
    ++w->step_calls;
    if (dt > w->max_step_dt) w->max_step_dt = dt;
    double remaining = dt;
    const double quantum = 1.0 / 120.0;
    while (remaining > 1e-12 && !w->done) {
        double h = remaining < quantum ? remaining : quantum;
        w->sim_time += h;
        if (!w->panel_open) move_player(w, h);
        move_objects(w, h);
        update_watchers(w);
        if (!w->done) maybe_finish(w);
        ++w->internal_steps;
        remaining -= h;
    }
}

void ow_key(OwWorld *w, int key, int down) {
    if (w->done) return;
    ++w->actions; ++w->key_events;
    switch (key) {
        case 'w': case 'W': w->key_w = down; break;
        case 'a': case 'A': w->key_a = down; break;
        case 's': case 'S': w->key_s = down; break;
        case 'd': case 'D': w->key_d = down; break;
        case 27:
            if (down && w->panel_open) {
                w->panel_open = 0; w->active_station = -1; w->drag_piece = -1;
                log_event(w, EV_PANEL_CLOSE, 0, 0, 0, 0);
            }
            break;
        default: break;
    }
}

void ow_text(OwWorld *w, char ch) {
    if (w->done || !w->panel_open || w->active_station < 0) return;
    if (w->stations[w->active_station].kind != OW_STATION_TERMINAL || w->terminal_complete) return;
    if (ch >= 'a' && ch <= 'z') ch = (char)(ch - 'a' + 'A');
    if (!((ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9'))) return;
    if (w->typed_len >= OW_CODE_MAX - 1) return;
    w->typed_code[w->typed_len++] = ch;
    w->typed_code[w->typed_len] = 0;
    ++w->actions; ++w->key_events;
}

void ow_backspace(OwWorld *w) {
    if (w->typed_len > 0 && w->panel_open && w->active_station >= 0 &&
        w->stations[w->active_station].kind == OW_STATION_TERMINAL) {
        --w->typed_len; w->typed_code[w->typed_len] = 0;
        ++w->actions; ++w->key_events;
    }
}

void ow_enter(OwWorld *w) {
    if (!w->panel_open || w->active_station < 0 || w->stations[w->active_station].kind != OW_STATION_TERMINAL) return;
    if (!task_unlocked(w, OW_TASK_TRANSFER) || w->terminal_complete) return;
    ++w->actions; ++w->key_events;
    if (!strcmp(w->typed_code, w->source_code)) {
        w->terminal_complete = 1;
        log_event(w, EV_TERMINAL_OK, w->typed_len, 0, 0, 0);
        mark_recovered(w, OW_TASK_TRANSFER);
    } else {
        ++w->wrong_actions;
        log_event(w, EV_TERMINAL_BAD, w->typed_len, 0, 0, 0);
        w->typed_len = 0; w->typed_code[0] = 0;
        recoverable_error(w, OW_FAIL_TERMINAL_BAD, 0, 0);
        return;
    }
    maybe_finish(w);
}

static int watcher_visual_slot(const OwWorld *w, int idx) {
    if (w->watcher_count <= 1) return idx;
    static const int mults[6] = {1,3,5,7,11,13};
    int m = mults[w->presentation_family % 6];
    while (m < w->watcher_count && (w->watcher_count % m) == 0) m += 2;
    int off = (int)((w->presentation_family * 7u) % (unsigned)w->watcher_count);
    return (idx * m + off) % w->watcher_count;
}

static void watcher_tile_rect(const OwWorld *w, int idx, int *x, int *y, int *tw, int *th) {
    int slot = watcher_visual_slot(w, idx);
    int mode = w->presentation_family % 4;
    if (mode == 0) {
        int cols=32; *tw=17; *th=19;
        *x=6+(slot%cols)*(*tw); *y=6+(slot/cols)*(*th);
    } else if (mode == 1) {
        *tw=14; *th=16;
        if (slot < 32) { int j=slot; *x=4+(j%2)*15; *y=OW_HUD_H+4+(j/2)*18; }
        else { int j=slot-32; *x=OW_WIDTH-34+(j%2)*15; *y=OW_HUD_H+4+(j/2)*18; }
    } else if (mode == 2) {
        *tw=14; *th=15;
        int corner=slot/16, j=slot%16, gx=j%4, gy=j/4;
        int bx=(corner&1)?OW_WIDTH-64:4, by=(corner&2)?OW_HEIGHT-66:4;
        *x=bx+gx*15; *y=by+gy*16;
    } else {
        *tw=19; *th=17;
        if (slot < 32) { *x=16+(slot%32)*19; *y=5; }
        else { *x=16+((slot-32)%32)*19; *y=OW_HEIGHT-22; }
    }
}

static int watcher_tile_at(const OwWorld *w, float x, float y) {
    for (int i=0;i<w->watcher_count;++i) {
        int tx,ty,tw,th; watcher_tile_rect(w,i,&tx,&ty,&tw,&th);
        if (x >= tx+1 && x <= tx+tw-2 && y >= ty+1 && y <= ty+th-2) return i;
    }
    return -1;
}

static int focused_station(const OwWorld *w) {
    int best = -1;
    float best_score = 1e9f;
    for (int i = 0; i < w->station_count; ++i) {
        uint8_t bit = station_task_bit(w->stations[i].kind);
        if (bit && (!task_unlocked(w, bit) || task_complete(w, bit))) continue;
        float dx = w->stations[i].x - w->px, dy = w->stations[i].y - w->py;
        float dist = hypotf(dx, dy);
        if (dist > 1.65f || !visible_line(w, w->px, w->py, w->stations[i].x, w->stations[i].y)) continue;
        float a = atan2f(dy, dx) - w->angle;
        while (a > (float)M_PI) a -= (float)(2*M_PI);
        while (a < (float)-M_PI) a += (float)(2*M_PI);
        float score = fabsf(a) + dist * 0.04f;
        if (fabsf(a) < 0.22f && score < best_score) { best = i; best_score = score; }
    }
    return best;
}

static int focused_object(const OwWorld *w) {
    int best = -1;
    float best_dist = 1e9f;
    for (int i=0;i<w->object_count;++i) {
        const OwObject *o=&w->objects[i];
        if (!o->active) continue;
        float dx=o->x-w->px, dy=o->y-w->py;
        float dist=hypotf(dx,dy);
        if (dist >= 12.0f || dist >= best_dist) continue;
        float a=atan2f(dy,dx)-w->angle;
        while(a>(float)M_PI)a-=(float)(2*M_PI);
        while(a<(float)-M_PI)a+=(float)(2*M_PI);
        float angular=atanf(w->d.object_radius/(dist>0.05f?dist:0.05f));
        if (fabsf(a)<=angular*1.25f && visible_line(w,w->px,w->py,o->x,o->y)) { best=i; best_dist=dist; }
    }
    return best;
}

static int piece_at(const OwWorld *w, float x, float y) {
    for (int i = w->piece_count - 1; i >= 0; --i) {
        const OwPiece *p = &w->pieces[i];
        if (p->placed) continue;
        if (hypotf(x - p->x, y - p->y) <= 20.0f) return i;
    }
    return -1;
}

void ow_mouse_move(OwWorld *w, float dx, float dy, float x, float y) {
    (void)dy;
    w->cursor_x = x; w->cursor_y = y;
    if (w->done) return;
    if (w->panel_open && w->drag_piece >= 0) {
        OwPiece *p = &w->pieces[w->drag_piece];
        p->x = clampf(x, OW_PANEL_X + 20.0f, OW_PANEL_X + OW_PANEL_W - 20.0f);
        p->y = clampf(y, OW_PANEL_Y + 20.0f, OW_PANEL_Y + OW_PANEL_H - 20.0f);
        ++w->pointer_events;
    } else if (!w->panel_open && y >= OW_HUD_H && watcher_tile_at(w,x,y) < 0) {
        w->angle += dx * w->d.mouse_gain;
        while (w->angle > (float)M_PI) w->angle -= (float)(2*M_PI);
        while (w->angle < (float)-M_PI) w->angle += (float)(2*M_PI);
    }
}

void ow_mouse_button(OwWorld *w, int button, int down, float x, float y) {
    if (w->done) return;
    ++w->actions; ++w->pointer_events;
    w->cursor_x = x; w->cursor_y = y;
    if (button == 3 && down && w->panel_open) {
        w->panel_open = 0; w->active_station = -1; w->drag_piece = -1;
        log_event(w, EV_PANEL_CLOSE, 0, 0, x, y);
        return;
    }
    if (button != 1) return;

    int wi = watcher_tile_at(w, x, y);
    if (wi >= 0 && down) {
        OwWatcher *q = &w->watchers[wi];
        if (q->alert) {
            q->alert = 0; q->acknowledged = 1; q->ack_flash_until = w->sim_time + 0.25;
            ++w->alerts_acked;
            log_event(w, EV_ALERT_ACK, wi, (int)q->generation, x, y);
            mark_recovered(w, OW_TASK_ALERTS);
            maybe_finish(w);
        } else {
            ++w->false_acks; ++w->wrong_actions;
            fail_agent(w, OW_FAIL_FORBIDDEN_ACTION, EV_WATCHER_FALSE_ACK, wi, (int)q->generation, x, y);
        }
        return;
    }

    if (!w->panel_open) {
        if (!down) return;
        int st = focused_station(w);
        if (st >= 0) {
            w->panel_open = 1; w->active_station = st; w->drag_piece = -1;
            log_event(w, EV_PANEL_OPEN, w->stations[st].kind, st, x, y);
            return;
        }
        int obj = focused_object(w);
        if (obj >= 0) {
            if (!task_unlocked(w, OW_TASK_TARGET) || w->target_complete || obj != w->target_object) {
                ++w->wrong_actions;
                fail_agent(w, OW_FAIL_FORBIDDEN_ACTION, EV_WRONG_TARGET, obj, w->target_object, w->objects[obj].x, w->objects[obj].y);
                return;
            }
            int t = obj;
            ++w->target_hits;
            log_event(w, EV_TARGET_HIT, w->target_hits, t, w->objects[t].x, w->objects[t].y);
            mark_recovered(w, OW_TASK_TARGET);
            if (w->target_hits >= w->target_hits_required) w->target_complete = 1;
            else {
                w->objects[t].x = w->target_reloc_x;
                w->objects[t].y = w->target_reloc_y;
                log_event(w, EV_TARGET_RELOCATE, t, w->target_hits, w->target_reloc_x, w->target_reloc_y);
            }
            maybe_finish(w);
        } else {
            ++w->motor_misses;
            log_event(w, EV_MOTOR_MISS, 0, 0, x, y);
            recoverable_error(w, OW_FAIL_MOTOR_MISS, x, y);
        }
        return;
    }

    if (w->active_station < 0) return;
    OwStationKind kind = (OwStationKind)w->stations[w->active_station].kind;
    if (kind == OW_STATION_ASSEMBLY) {
        if (down) {
            w->drag_piece = piece_at(w, x, y);
            if (w->drag_piece < 0) {
                ++w->motor_misses;
                log_event(w, EV_MOTOR_MISS, 1, 0, x, y);
                recoverable_error(w, OW_FAIL_MOTOR_MISS, x, y);
            }
        } else if (w->drag_piece >= 0) {
            OwPiece *p = &w->pieces[w->drag_piece];
            float err = hypotf(p->x - p->slot_x, p->y - p->slot_y);
            if (err <= w->d.assembly_tolerance) {
                p->x = p->slot_x; p->y = p->slot_y; p->placed = 1;
                log_event(w, EV_ASSEMBLY_PLACE, w->drag_piece, 0, p->x, p->y);
                mark_recovered(w, OW_TASK_ASSEMBLY);
            } else {
                ++w->wrong_actions;
                int piece=w->drag_piece;
                log_event(w, EV_ASSEMBLY_MISS, piece, 0, p->x, p->y);
                p->x=p->home_x; p->y=p->home_y;
                w->drag_piece=-1;
                recoverable_error(w, OW_FAIL_ASSEMBLY_MISS, p->x, p->y);
                return;
            }
            w->drag_piece = -1;
            int all = 1;
            for (int i = 0; i < w->piece_count; ++i) if (!w->pieces[i].placed) all = 0;
            w->assembly_complete = all;
            maybe_finish(w);
        }
    }
}

/* ---------- software renderer ---------- */
