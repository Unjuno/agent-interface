static uint32_t rgb(unsigned r, unsigned g, unsigned b) { return 0xff000000u | (r<<16) | (g<<8) | b; }
static uint32_t COLORS[6] = {0xff3b82f6u,0xffef4444u,0xff22c55eu,0xffeab308u,0xffa855f7u,0xfff97316u};

static void px(OwFrame *f, int x, int y, uint32_t c) {
    if ((unsigned)x < OW_WIDTH && (unsigned)y < OW_HEIGHT) f->pixels[y*OW_WIDTH+x] = c;
}
static void rect(OwFrame *f, int x, int y, int w, int h, uint32_t c) {
    int x0=x<0?0:x, y0=y<0?0:y, x1=x+w>OW_WIDTH?OW_WIDTH:x+w, y1=y+h>OW_HEIGHT?OW_HEIGHT:y+h;
    for(int yy=y0;yy<y1;++yy){uint32_t *p=&f->pixels[yy*OW_WIDTH+x0];for(int xx=x0;xx<x1;++xx)*p++=c;}
}
static void box(OwFrame *f,int x,int y,int w,int h,uint32_t fill,uint32_t outline){rect(f,x,y,w,h,fill);rect(f,x,y,w,2,outline);rect(f,x,y+h-2,w,2,outline);rect(f,x,y,2,h,outline);rect(f,x+w-2,y,2,h,outline);}
static void line(OwFrame *f,int x0,int y0,int x1,int y1,uint32_t c){int dx=abs(x1-x0),sx=x0<x1?1:-1,dy=-abs(y1-y0),sy=y0<y1?1:-1,e=dx+dy;for(;;){px(f,x0,y0,c);if(x0==x1&&y0==y1)break;int e2=2*e;if(e2>=dy){e+=dy;x0+=sx;}if(e2<=dx){e+=dx;y0+=sy;}}}
static void circle(OwFrame *f,int cx,int cy,int r,uint32_t c,int fill){for(int y=-r;y<=r;++y)for(int x=-r;x<=r;++x){int d=x*x+y*y;if(fill?d<=r*r:(d<=r*r&&d>=(r-2)*(r-2)))px(f,cx+x,cy+y,c);}}
static void diamond(OwFrame *f,int cx,int cy,int r,uint32_t c,int fill){for(int y=-r;y<=r;++y){int span=r-abs(y);if(fill)for(int x=-span;x<=span;++x)px(f,cx+x,cy+y,c);else{px(f,cx-span,cy+y,c);px(f,cx+span,cy+y,c);}}}
static void shape(OwFrame *f,int cx,int cy,int r,int s,uint32_t c,int fill){if(s==0)circle(f,cx,cy,r,c,fill);else if(s==1){if(fill)rect(f,cx-r,cy-r,2*r+1,2*r+1,c);else box(f,cx-r,cy-r,2*r+1,2*r+1,0xff10151cu,c);}else if(s==2){for(int y=0;y<=2*r;++y){int span=y/2;if(fill)for(int x=-span;x<=span;++x)px(f,cx+x,cy-r+y,c);else{px(f,cx-span,cy-r+y,c);px(f,cx+span,cy-r+y,c);}}}else diamond(f,cx,cy,r,c,fill);}

/* 5-column glyphs, low 7 bits are rows. */
static const uint8_t *glyph(char ch) {
    static uint8_t g[5]; memset(g,0,5);
#define G(a,b,c,d,e) do{g[0]=a;g[1]=b;g[2]=c;g[3]=d;g[4]=e;return g;}while(0)
    switch(ch){
    case 'A':G(0x7e,0x09,0x09,0x09,0x7e); case 'B':G(0x7f,0x49,0x49,0x49,0x36);
    case 'C':G(0x3e,0x41,0x41,0x41,0x22); case 'D':G(0x7f,0x41,0x41,0x22,0x1c);
    case 'E':G(0x7f,0x49,0x49,0x49,0x41); case 'F':G(0x7f,0x09,0x09,0x09,0x01);
    case 'G':G(0x3e,0x41,0x49,0x49,0x7a); case 'H':G(0x7f,0x08,0x08,0x08,0x7f);
    case 'I':G(0x41,0x41,0x7f,0x41,0x41); case 'J':G(0x20,0x40,0x41,0x3f,0x01);
    case 'K':G(0x7f,0x08,0x14,0x22,0x41); case 'L':G(0x7f,0x40,0x40,0x40,0x40);
    case 'M':G(0x7f,0x02,0x0c,0x02,0x7f); case 'N':G(0x7f,0x04,0x08,0x10,0x7f);
    case 'O':G(0x3e,0x41,0x41,0x41,0x3e); case 'P':G(0x7f,0x09,0x09,0x09,0x06);
    case 'Q':G(0x3e,0x41,0x51,0x21,0x5e); case 'R':G(0x7f,0x09,0x19,0x29,0x46);
    case 'S':G(0x46,0x49,0x49,0x49,0x31); case 'T':G(0x01,0x01,0x7f,0x01,0x01);
    case 'U':G(0x3f,0x40,0x40,0x40,0x3f); case 'V':G(0x1f,0x20,0x40,0x20,0x1f);
    case 'W':G(0x7f,0x20,0x18,0x20,0x7f); case 'X':G(0x63,0x14,0x08,0x14,0x63);
    case 'Y':G(0x07,0x08,0x70,0x08,0x07); case 'Z':G(0x61,0x51,0x49,0x45,0x43);
    case '0':G(0x3e,0x51,0x49,0x45,0x3e); case '1':G(0x00,0x42,0x7f,0x40,0x00);
    case '2':G(0x42,0x61,0x51,0x49,0x46); case '3':G(0x21,0x41,0x45,0x4b,0x31);
    case '4':G(0x18,0x14,0x12,0x7f,0x10); case '5':G(0x27,0x45,0x45,0x45,0x39);
    case '6':G(0x3c,0x4a,0x49,0x49,0x30); case '7':G(0x01,0x71,0x09,0x05,0x03);
    case '8':G(0x36,0x49,0x49,0x49,0x36); case '9':G(0x06,0x49,0x49,0x29,0x1e);
    case ':':G(0,0x36,0x36,0,0); case '-':G(0x08,0x08,0x08,0x08,0x08);
    case '/':G(0x60,0x18,0x06,0x01,0); case '>':G(0x41,0x22,0x14,0x08,0);
    case '_':G(0x40,0x40,0x40,0x40,0x40); case '+':G(0x08,0x08,0x3e,0x08,0x08);
    default:G(0,0,0,0,0);
    }
#undef G
}
static void text(OwFrame *f,int x,int y,int scale,const char *s,uint32_t c){for(;*s;++s){char ch=*s;if(ch>='a'&&ch<='z')ch=(char)(ch-'a'+'A');const uint8_t*g=glyph(ch);for(int col=0;col<5;++col)for(int row=0;row<7;++row)if(g[col]&(1u<<row))rect(f,x+col*scale,y+row*scale,scale,scale,c);x+=6*scale;}}

static uint32_t shade(uint32_t c,float k){unsigned r=(c>>16)&255,g=(c>>8)&255,b=c&255;r=(unsigned)(r*k);g=(unsigned)(g*k);b=(unsigned)(b*k);return rgb(r,g,b);}

static void render_station_icon(OwFrame *f, uint8_t kind, uint8_t style, int screen, int cy, int r, uint32_t ic) {
    if (kind == OW_STATION_SOURCE) {
        if (style == 0) { box(f,screen-r*2,cy-r,r*2,r*2,rgb(15,23,42),ic); box(f,screen+1,cy-r,r*2,r*2,rgb(15,23,42),ic); }
        else if (style == 1) { box(f,screen-r,cy-r*2,r*2,r*2,rgb(15,23,42),ic); box(f,screen-r,cy+1,r*2,r*2,rgb(15,23,42),ic); }
        else { diamond(f,screen-r,cy,r,ic,0); diamond(f,screen+r,cy,r,ic,0); line(f,screen-r/2,cy,screen+r/2,cy,ic); }
    } else if (kind == OW_STATION_TERMINAL) {
        if (style == 0) { line(f,screen-r*2,cy+r,screen+r*2,cy+r,ic); line(f,screen-r*2,cy-r,screen-r/2,cy,ic); line(f,screen-r*2,cy+r,screen-r/2,cy,ic); }
        else if (style == 1) { box(f,screen-r*2,cy-r,r*4,r*2,rgb(15,23,42),ic); line(f,screen-r,cy,screen+r,cy,ic); }
        else { line(f,screen-r*2,cy,screen+r*2,cy,ic); line(f,screen+r,cy-r,screen+r*2,cy,ic); line(f,screen+r,cy+r,screen+r*2,cy,ic); }
    } else if (kind == OW_STATION_ASSEMBLY) {
        int sh = style == 0 ? 1 : (style == 1 ? 3 : 0);
        shape(f,screen-r,cy,r,sh,ic,1); shape(f,screen+r*2,cy,r,sh,ic,0);
    } else if (kind == OW_STATION_MONITOR) {
        if (style == 0) for(int gy=0;gy<2;++gy)for(int gx=0;gx<2;++gx) box(f,screen-r*2+gx*(r*2+1),cy-r*2+gy*(r*2+1),r*2-1,r*2-1,rgb(15,23,42),ic);
        else if (style == 1) { box(f,screen-r*2,cy-r,r*4,r*2,rgb(15,23,42),ic); line(f,screen-r,cy,screen-r/2,cy-r/2,ic); line(f,screen-r/2,cy-r/2,screen,cy+r/2,ic); line(f,screen,cy+r/2,screen+r,cy-r/2,ic); }
        else { circle(f,screen,cy,r*2,ic,0); for(int a=0;a<4;++a){int dx=(a&1)?r:-r,dy=(a&2)?r:-r;circle(f,screen+dx,cy+dy,r/2,ic,1);} }
    }
}

static void render_world(OwWorld *w, OwFrame *f) {
    rect(f,0,0,OW_WIDTH,OW_HEIGHT,rgb(14,20,28));
    rect(f,0,OW_HUD_H,OW_WIDTH,(OW_HEIGHT-OW_HUD_H)/2,rgb(25,36,50));
    rect(f,0,OW_HUD_H+(OW_HEIGHT-OW_HUD_H)/2,OW_WIDTH,(OW_HEIGHT-OW_HUD_H)/2,rgb(36,42,46));
    float dirx=cosf(w->angle),diry=sinf(w->angle),planex=-diry*tanf((float)OW_FOV/2),planey=dirx*tanf((float)OW_FOV/2);
    for(int x=0;x<OW_WIDTH;++x){
        float cam=2.0f*x/(float)OW_WIDTH-1.0f, rx=dirx+planex*cam, ry=diry+planey*cam;
        int mx=(int)w->px,my=(int)w->py;float ddx=fabsf(1.0f/(fabsf(rx)<1e-6f?1e-6f:rx)),ddy=fabsf(1.0f/(fabsf(ry)<1e-6f?1e-6f:ry));
        int stepx,stepy;float sdx,sdy; if(rx<0){stepx=-1;sdx=(w->px-mx)*ddx;}else{stepx=1;sdx=(mx+1.0f-w->px)*ddx;} if(ry<0){stepy=-1;sdy=(w->py-my)*ddy;}else{stepy=1;sdy=(my+1.0f-w->py)*ddy;}
        int side=0; for(int guard=0;guard<64;++guard){if(sdx<sdy){sdx+=ddx;mx+=stepx;side=0;}else{sdy+=ddy;my+=stepy;side=1;}if(mx<0||my<0||mx>=OW_MAP_W||my>=OW_MAP_H||w->map[my][mx])break;}
        float dist=side==0?(mx-w->px+(1-stepx)/2.0f)/(fabsf(rx)<1e-6f?1e-6f:rx):(my-w->py+(1-stepy)/2.0f)/(fabsf(ry)<1e-6f?1e-6f:ry);
        if (dist < 0.05f) dist = 0.05f;
        f->zbuf[x] = dist;
        int lh = (int)((OW_HEIGHT - OW_HUD_H) / dist);
        if (lh > OW_HEIGHT - OW_HUD_H) lh = OW_HEIGHT - OW_HUD_H;
        int y0 = OW_HUD_H + (OW_HEIGHT - OW_HUD_H - lh) / 2;
        float k=clampf(1.0f/(0.38f+dist*0.12f),0.22f,1.0f)*(side?0.78f:1.0f);uint32_t wc=shade(rgb(110,134,151),k);rect(f,x,y0,1,lh,wc);
    }
    for(int pass=0;pass<2;++pass){
        for(int i=0;i<w->station_count;++i){
            float sx=w->stations[i].x-w->px,sy=w->stations[i].y-w->py;
            float inv=1.0f/(planex*diry-dirx*planey);
            float tx=inv*(diry*sx-dirx*sy),ty=inv*(-planey*sx+planex*sy);
            if(ty<=0.15f)continue;
            int screen=(int)((OW_WIDTH/2)*(1+tx/ty));
            int h=(int)(120.0f/ty); int ww=h/2;
            if (h < 8) h = 8;
            if (ww < 5) ww = 5;
            int x0=screen-ww/2,y0=OW_HUD_H+(OW_HEIGHT-OW_HUD_H)/2-h/2;
            uint8_t bit=station_task_bit(w->stations[i].kind);
            int powered=!bit || (task_unlocked(w,bit) && !task_complete(w,bit));
            uint32_t cc=COLORS[w->stations[i].color%6];
            float state_k=powered?1.0f:0.28f;
            for(int xx=x0;xx<x0+ww;++xx)
                if(xx>=0&&xx<OW_WIDTH&&ty<f->zbuf[xx])
                    rect(f,xx,y0,1,h,shade(cc,clampf(1.2f/(0.6f+ty*0.15f),0.3f,1.0f)*state_k));
            if(screen>=0&&screen<OW_WIDTH&&ty<f->zbuf[screen]&&h>=18){
                int cy=y0+h/2, r=h/8; if(r<2)r=2; uint32_t ic=powered?rgb(241,245,249):rgb(100,116,139);
                render_station_icon(f,w->stations[i].kind,w->stations[i].icon_style,screen,cy,r,ic);
            }
        }
        for(int i=0;i<w->object_count;++i){OwObject*o=&w->objects[i];float sx=o->x-w->px,sy=o->y-w->py;float inv=1.0f/(planex*diry-dirx*planey);float tx=inv*(diry*sx-dirx*sy),ty=inv*(-planey*sx+planex*sy);if(ty<=0.1f)continue;int screen=(int)((OW_WIDTH/2)*(1+tx/ty));int rr=(int)(w->d.object_radius*180.0f/ty);rr=rr<2?2:(rr>40?40:rr);if(screen+rr<0||screen-rr>=OW_WIDTH)continue;uint32_t cc=COLORS[o->color%6];if(screen>=0&&screen<OW_WIDTH&&ty<f->zbuf[screen])shape(f,screen,OW_HUD_H+(OW_HEIGHT-OW_HUD_H)/2,rr,o->shape,cc,1);}
    }
    int cx=OW_WIDTH/2,cy=OW_HUD_H+(OW_HEIGHT-OW_HUD_H)/2;line(f,cx-7,cy,cx+7,cy,0xffffffffu);line(f,cx,cy-7,cx,cy+7,0xffffffffu);
}

static uint32_t alert_color(const OwWorld *w) {
    static const uint32_t a[4]={0xffdc2626u,0xff06b6d4u,0xfff97316u,0xffd946efu};
    return a[(w->presentation_family/3)%4];
}

static void render_watchers(OwWorld *w, OwFrame *f){
    for(int i=0;i<w->watcher_count;++i){
        int x,y,tw,th; watcher_tile_rect(w,i,&x,&y,&tw,&th);
        uint32_t fill=w->watchers[i].alert?alert_color(w):((w->watchers[i].acknowledged&&w->sim_time<w->watchers[i].ack_flash_until)?rgb(22,163,74):rgb(39,51,66));
        box(f,x,y,tw-1,th-1,fill,rgb(100,116,139));
        if(w->watchers[i].alert){double rem=w->watchers[i].deadline-w->sim_time;float frac=(float)clampd(rem/w->d.alert_deadline,0,1);rect(f,x+2,y+th-4,(int)((tw-5)*frac),2,rgb(241,245,249));}
    }
}

static void render_task_cues(OwWorld *w, OwFrame *f){
    if (!task_required(w,OW_TASK_TARGET) || !task_unlocked(w,OW_TASK_TARGET) || w->target_complete) return;
    OwObject *o=&w->objects[w->target_object];
    int mode=w->presentation_family%4, cx=OW_WIDTH/2, cy=OW_HEIGHT-24;
    if(mode==1){cx=OW_WIDTH/2;cy=27;} else if(mode==2){cx=OW_WIDTH/2;cy=27;} else if(mode==3){cx=52;cy=OW_HEIGHT/2;}
    box(f,cx-27,cy-19,54,38,rgb(23,32,43),rgb(148,163,184));
    shape(f,cx,cy,11,o->shape,COLORS[o->color],1);
}

static void render_source_panel(OwWorld*w,OwFrame*f){box(f,OW_PANEL_X,OW_PANEL_Y,OW_PANEL_W,OW_PANEL_H,rgb(20,30,42),rgb(59,130,246));box(f,OW_PANEL_X+85,OW_PANEL_Y+80,OW_PANEL_W-170,80,rgb(9,14,22),rgb(100,116,139));int scale=4;int tw=(int)strlen(w->source_code)*6*scale;text(f,OW_WIDTH/2-tw/2,OW_PANEL_Y+103,scale,w->source_code,rgb(241,245,249));}
static void render_terminal_panel(OwWorld*w,OwFrame*f){box(f,OW_PANEL_X,OW_PANEL_Y,OW_PANEL_W,OW_PANEL_H,rgb(20,30,42),rgb(59,130,246));box(f,OW_PANEL_X+75,OW_PANEL_Y+95,OW_PANEL_W-150,58,rgb(5,10,16),w->terminal_complete?rgb(34,197,94):rgb(148,163,184));char buf[OW_CODE_MAX+2];snprintf(buf,sizeof(buf),"%s_",w->typed_code);text(f,OW_PANEL_X+95,OW_PANEL_Y+111,3,buf,rgb(241,245,249));}
static void render_assembly_panel(OwWorld*w,OwFrame*f){box(f,OW_PANEL_X,OW_PANEL_Y,OW_PANEL_W,OW_PANEL_H,rgb(20,30,42),rgb(168,85,247));line(f,OW_PANEL_X+OW_PANEL_W/2,OW_PANEL_Y+18,OW_PANEL_X+OW_PANEL_W/2,OW_PANEL_Y+OW_PANEL_H-18,rgb(51,65,85));for(int i=0;i<w->piece_count;++i){OwPiece*p=&w->pieces[i];shape(f,(int)p->slot_x,(int)p->slot_y,17,p->shape,COLORS[p->color],0);shape(f,(int)p->x,(int)p->y,15,p->shape,COLORS[p->color],1);}}
static void render_monitor_panel(OwWorld*w,OwFrame*f){box(f,OW_PANEL_X,OW_PANEL_Y,OW_PANEL_W,OW_PANEL_H,rgb(20,30,42),rgb(34,197,94));int cols=8;int tw=48,th=24;for(int i=0;i<w->watcher_count;++i){int row=i/cols,col=i%cols;int x=OW_PANEL_X+45+col*tw,y=OW_PANEL_Y+28+row*th;uint32_t c=w->watchers[i].alert?rgb(220,38,38):(w->watchers[i].acknowledged?rgb(22,101,52):rgb(51,65,85));box(f,x,y,tw-8,th-5,c,rgb(148,163,184));}}

static void render_pointer_cursor(OwWorld*w,OwFrame*f){
    if (!(w->panel_open || w->cursor_y < OW_HUD_H || watcher_tile_at(w,w->cursor_x,w->cursor_y) >= 0)) return;
    int x=(int)w->cursor_x,y=(int)w->cursor_y;
    uint32_t c=rgb(248,250,252);
    line(f,x,y,x+10,y+15,c); line(f,x,y,x+2,y+11,c); line(f,x+2,y+11,x+6,y+9,c);
}

void ow_render(OwWorld *w, OwFrame *f) {
    render_world(w,f);
    render_watchers(w,f);
    render_task_cues(w,f);
    if(w->panel_open&&w->active_station>=0){switch(w->stations[w->active_station].kind){case OW_STATION_SOURCE:render_source_panel(w,f);break;case OW_STATION_TERMINAL:render_terminal_panel(w,f);break;case OW_STATION_ASSEMBLY:render_assembly_panel(w,f);break;case OW_STATION_MONITOR:render_monitor_panel(w,f);break;default:break;}}
    render_pointer_cursor(w,f);
    if(w->done){box(f,OW_WIDTH/2-150,OW_HEIGHT/2-42,300,84,rgb(23,32,43),rgb(100,116,139));text(f,OW_WIDTH/2-16*6,OW_HEIGHT/2-7,2,"SESSION COMPLETE",rgb(203,213,225));}
}

int ow_write_ppm(const char *path, const OwFrame *f) {
    FILE *fp=fopen(path,"wb"); if(!fp)return -1; fprintf(fp,"P6\n%d %d\n255\n",OW_WIDTH,OW_HEIGHT); for(int i=0;i<OW_WIDTH*OW_HEIGHT;++i){uint32_t c=f->pixels[i];unsigned char b[3]={(unsigned char)(c>>16),(unsigned char)(c>>8),(unsigned char)c};fwrite(b,1,3,fp);} fclose(fp);return 0;
}

static const char *failure_name(uint16_t c){switch(c){
    case OW_FAIL_NONE:return "none";
    case OW_FAIL_EPISODE_TIMEOUT:return "episode_timeout";
    case OW_FAIL_MISSED_ALERT:return "missed_alert";
    case OW_FAIL_FORBIDDEN_ACTION:return "forbidden_action";
    case OW_FAIL_MOTOR_MISS:return "motor_miss";
    case OW_FAIL_TERMINAL_BAD:return "terminal_bad_submit";
    case OW_FAIL_ASSEMBLY_MISS:return "assembly_miss";
    case OW_FAIL_RECOVERY_EXHAUSTED:return "recovery_exhausted";
    case OW_FAIL_EPISODE_GENERATION:return "episode_generation";
    case OW_FAIL_EVENT_OVERFLOW:return "instrument_event_overflow";
    default:return "unknown";
}}
int ow_report_json(const OwWorld *w, const char *path) {
    FILE *fp=fopen(path,"w"); if(!fp)return -1;
    double wall_elapsed=mono_time()-w->started_wall;
    fprintf(fp,"{\n  \"schema\": \"procedural-operations-world-report-v0.2\",\n  \"seed\": %llu,\n  \"family_key\": %llu,\n  \"episode_hash\": \"%016llx\",\n",
            (unsigned long long)w->seed,(unsigned long long)w->family_key,(unsigned long long)w->episode_hash);
    fprintf(fp,"  \"done\": %s,\n  \"success\": %s,\n  \"failure\": \"%s\",\n  \"sim_time\": %.6f,\n  \"wall_time\": %.6f,\n",
            w->done?"true":"false",w->success?"true":"false",failure_name(w->failure_code),w->sim_time,wall_elapsed);
    fprintf(fp,"  \"timing\": {\"max_external_dt\": %.6f, \"step_calls\": %llu, \"internal_steps\": %llu},\n",
            w->max_step_dt,(unsigned long long)w->step_calls,(unsigned long long)w->internal_steps);
    fprintf(fp,"  \"difficulty\": {\"target_speed\": %.6f, \"object_radius\": %.6f, \"object_count\": %d, \"watcher_count\": %d, \"event_rate\": %.6f, \"alert_deadline\": %.6f, \"alert_burst\": %d, \"required_alerts\": %d, \"typing_length\": %d, \"assembly_pieces\": %d, \"assembly_tolerance\": %.6f, \"navigation_speed\": %.6f, \"mouse_gain\": %.8f, \"episode_seconds\": %.6f, \"work_task_count\": %d, \"dependency_depth\": %d, \"recovery_budget\": %d},\n",
            w->d.target_speed,w->d.object_radius,w->d.object_count,w->d.watcher_count,w->d.event_rate,w->d.alert_deadline,w->d.alert_burst,w->d.required_alerts,w->d.typing_length,w->d.assembly_pieces,w->d.assembly_tolerance,w->d.navigation_speed,w->d.mouse_gain,w->d.episode_seconds,w->d.work_task_count,w->d.dependency_depth,w->d.recovery_budget);
    fprintf(fp,"  \"generation\": {\"map_variant\": %u, \"map_openings_mask\": %u, \"presentation_family\": %u, \"task_mask\": %u, \"task_graph_variant\": %u, \"task_order\": [%u,%u,%u], \"task_deps\": [%u,%u,%u]},\n",
            (unsigned)w->map_variant,(unsigned)w->map_openings_mask,(unsigned)w->presentation_family,(unsigned)w->task_mask,(unsigned)w->task_graph_variant,
            (unsigned)w->task_order[0],(unsigned)w->task_order[1],(unsigned)w->task_order[2],(unsigned)w->task_deps[0],(unsigned)w->task_deps[1],(unsigned)w->task_deps[2]);
    fprintf(fp,"  \"schedule\": {\"alerts\": %d, \"cursor\": %d, \"target_relocation\": [%.6f, %.6f], \"entries\": [",
            w->alert_schedule_count,w->alert_schedule_cursor,w->target_reloc_x,w->target_reloc_y);
    for(int i=0;i<w->alert_schedule_count;++i){const OwScheduledAlert*e=&w->alert_schedule[i];fprintf(fp,"%s{\"t\":%.6f,\"watcher\":%u,\"burst_slot\":%u}",i?",":"",e->t,(unsigned)e->watcher,(unsigned)e->burst_slot);}
    fprintf(fp,"]},\n");
    fprintf(fp,"  \"effects\": {\"terminal_complete\": %s, \"assembly_complete\": %s, \"target_complete\": %s, \"target_hits\": %d, \"alerts_spawned\": %d, \"alerts_acked\": %d, \"alerts_missed\": %d, \"recoverable_errors\": %llu, \"recoveries\": %llu},\n",
            w->terminal_complete?"true":"false",w->assembly_complete?"true":"false",w->target_complete?"true":"false",w->target_hits,w->alerts_spawned,w->alerts_acked,w->alerts_missed,(unsigned long long)w->recoverable_errors,(unsigned long long)w->recoveries);
    fprintf(fp,"  \"input\": {\"actions\": %llu, \"key_events\": %llu, \"pointer_events\": %llu, \"wrong_actions\": %llu, \"motor_misses\": %llu, \"false_acks\": %llu},\n",
            (unsigned long long)w->actions,(unsigned long long)w->key_events,(unsigned long long)w->pointer_events,(unsigned long long)w->wrong_actions,(unsigned long long)w->motor_misses,(unsigned long long)w->false_acks);
    fprintf(fp,"  \"event_ledger\": {\"count\": %d, \"capacity\": %d, \"overflow\": %s},\n",w->event_count,OW_MAX_EVENTS,w->event_overflow?"true":"false");
    fprintf(fp,"  \"events\": [\n");
    for(int i=0;i<w->event_count;++i){const OwEvent*e=&w->events[i];fprintf(fp,"    {\"t\": %.6f, \"type\": %u, \"a\": %d, \"b\": %d, \"x\": %.3f, \"y\": %.3f}%s\n",e->t,e->type,e->a,e->b,e->x,e->y,(i+1<w->event_count)?",":"");}
    fprintf(fp,"  ]\n}\n"); fclose(fp);return 0;
}

uint64_t ow_state_hash(const OwWorld *w) {
    uint64_t h=1469598103934665603ULL;
#define MIX(v) do{uint64_t _v=(uint64_t)(v);for(int _i=0;_i<8;++_i){h^=(uint8_t)(_v&255);h*=1099511628211ULL;_v>>=8;}}while(0)
    MIX(w->seed); MIX(w->family_key); MIX(w->map_variant); MIX(w->map_openings_mask); MIX(w->presentation_family);
    MIX(w->task_mask); MIX(w->task_graph_variant); for(int i=0;i<3;++i){MIX(w->task_order[i]);MIX(w->task_deps[i]);}
    MIX((uint64_t)llround(w->d.target_speed*100000)); MIX((uint64_t)llround(w->d.object_radius*100000)); MIX(w->d.object_count); MIX(w->d.watcher_count);
    MIX((uint64_t)llround(w->d.event_rate*100000)); MIX((uint64_t)llround(w->d.alert_deadline*100000)); MIX(w->d.alert_burst); MIX(w->d.required_alerts);
    MIX(w->d.typing_length); MIX(w->d.assembly_pieces); MIX((uint64_t)llround(w->d.assembly_tolerance*100000)); MIX(w->d.work_task_count); MIX(w->d.dependency_depth); MIX(w->d.recovery_budget);
    MIX((uint64_t)llround(w->px*100000)); MIX((uint64_t)llround(w->py*100000)); MIX((uint64_t)llround(w->angle*100000)); MIX((uint64_t)llround(w->sim_time*1000000));
    MIX(w->object_count); for(int i=0;i<w->object_count;++i){MIX((uint64_t)llround(w->objects[i].x*100000));MIX((uint64_t)llround(w->objects[i].y*100000));MIX((uint64_t)llround(w->objects[i].vx*100000));MIX((uint64_t)llround(w->objects[i].vy*100000));MIX(w->objects[i].color);MIX(w->objects[i].shape);}
    MIX((uint64_t)llround(w->target_reloc_x*100000)); MIX((uint64_t)llround(w->target_reloc_y*100000));
    MIX(w->watcher_count); for(int i=0;i<w->watcher_count;++i){MIX((uint64_t)llround(w->watchers[i].next_event*1000000));MIX(w->watchers[i].generation);MIX(w->watchers[i].alert);}
    MIX(w->alert_schedule_count); for(int i=0;i<w->alert_schedule_count;++i){MIX((uint64_t)llround(w->alert_schedule[i].t*1000000));MIX(w->alert_schedule[i].watcher);MIX(w->alert_schedule[i].burst_slot);}
    for(int i=0;i<w->station_count;++i){MIX((uint64_t)llround(w->stations[i].x*1000));MIX((uint64_t)llround(w->stations[i].y*1000));MIX(w->stations[i].kind);MIX(w->stations[i].color);MIX(w->stations[i].icon_style);}
    for(int i=0;i<w->piece_count;++i){MIX((uint64_t)llround(w->pieces[i].x*1000));MIX((uint64_t)llround(w->pieces[i].y*1000));MIX((uint64_t)llround(w->pieces[i].slot_x*1000));MIX((uint64_t)llround(w->pieces[i].slot_y*1000));MIX(w->pieces[i].color);MIX(w->pieces[i].shape);}
    for(const char*p=w->source_code;*p;++p)MIX((unsigned char)*p);
#undef MIX
    return h;
}
