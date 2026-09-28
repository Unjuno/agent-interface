#include "ops_world.h"
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    OwDifficulty d; ow_default_difficulty(&d);
    OwWorld w; ow_init(&w, 20260928, &d);
    OwFrame f; f.pixels = calloc((size_t)OW_WIDTH*OW_HEIGHT, sizeof(unsigned));
    if (!f.pixels) return 2;
    ow_render(&w,&f); ow_write_ppm("fixture-world.ppm",&f);
    const char *names[4]={"source","terminal","assembly","monitor"};
    for(int kind=0;kind<4;++kind){
        int idx=-1; for(int i=0;i<w.station_count;++i)if(w.stations[i].kind==kind){idx=i;break;}
        w.panel_open=1; w.active_station=idx;
        ow_render(&w,&f);
        char path[64]; snprintf(path,sizeof(path),"fixture-%s.ppm",names[kind]);
        ow_write_ppm(path,&f);
    }
    free(f.pixels);
    puts("5 render fixtures written");
    return 0;
}
