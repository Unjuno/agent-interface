#include "../../ops_world.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static uint64_t hash_pixels(const uint32_t *p, size_t n) {
    uint64_t h=1469598103934665603ULL;
    for(size_t i=0;i<n;++i){h^=p[i];h*=1099511628211ULL;}
    return h;
}

int main(void) {
    enum { SEEDS=256, FAMILIES=20, SAMPLE_SEED=234, PIXELS=OW_WIDTH*OW_HEIGHT };
    OwDifficulty d; ow_default_difficulty(&d);
    d.watcher_count=64; d.dependency_depth=0;
    OwFrame frame; frame.pixels=calloc(PIXELS,sizeof(uint32_t));
    if(!frame.pixels) return 2;
    uint64_t hashes[SEEDS][FAMILIES]; unsigned family_mask=0;
    uint8_t pres[SEEDS][FAMILIES]; unsigned cue_modes=0;
    size_t collisions=0, aliases=0, identical_pairs=0, distinct_full_hashes=0;
    uint64_t stride_collisions=0, stride_samples=0;
    for(uint64_t seed=0;seed<SEEDS;++seed) for(uint64_t fk=0;fk<FAMILIES;++fk){
        OwWorld w; ow_init_with_family(&w,seed,fk,&d);
        w.task_mask=OW_TASK_TARGET; w.task_deps[2]=0; w.target_complete=0;
        pres[seed][fk]=w.presentation_family;
        cue_modes|=1u<<(w.presentation_family%4);
        w.objects[w.target_object].active=1;
        ow_render(&w,&frame);
        uint64_t h=hash_pixels(frame.pixels,PIXELS); hashes[seed][fk]=h;
        family_mask|=1u<<(w.presentation_family%12);
        for(uint64_t prior=0;prior<fk;++prior) if(hashes[seed][prior]==h){
            if(pres[seed][prior]==pres[seed][fk]) ++aliases; else ++collisions;
        }
        if(seed==SAMPLE_SEED){
            uint64_t stride=1469598103934665603ULL;
            for(int i=0;i<PIXELS;i+=97){stride^=frame.pixels[i];stride*=1099511628211ULL;}
            for(uint64_t prior=0;prior<fk;++prior){
                OwWorld q; ow_init_with_family(&q,seed,prior,&d); q.task_mask=OW_TASK_TARGET; q.task_deps[2]=0;
                ow_render(&q,&frame);
                uint64_t other=1469598103934665603ULL;
                for(int i=0;i<PIXELS;i+=97){other^=frame.pixels[i];other*=1099511628211ULL;}
                ++stride_samples;
                if(other==stride) ++stride_collisions;
            }
        }
    }
    for(int f=0;f<FAMILIES;++f){
        int seen=0; for(int p=0;p<f;++p) if(hashes[SAMPLE_SEED][p]==hashes[SAMPLE_SEED][f]) seen=1;
        if(seen) ++identical_pairs; else ++distinct_full_hashes;
    }
    printf("schema=opsworld-presentation-full-frame-audit-v1\nseeds=%d\nfamilies_per_seed=%d\ncombinations=%d\nfamily_mask=0x%03x\ncue_mode_mask=0x%x\ndistinct_presentation_full_frame_collisions=%zu\nsame_presentation_key_aliases=%zu\n",
        SEEDS,FAMILIES,SEEDS*FAMILIES,family_mask,cue_modes,collisions,aliases);
    printf("sample_seed=%d\nsample_seed_distinct_full_frame_hashes=%zu\nsample_seed_duplicate_families=%zu\nsample_seed_stride97_colliding_pairs=%llu\nsample_seed_stride97_pairs=%llu\n",
        SAMPLE_SEED,distinct_full_hashes,identical_pairs,(unsigned long long)stride_collisions,(unsigned long long)stride_samples);
    printf("first_duplicate_pairs:");
    size_t printed=0;
    for(int seed=0;seed<SEEDS && printed<8;++seed) for(int a=0;a<FAMILIES && printed<8;++a) for(int b=a+1;b<FAMILIES && printed<8;++b)
        if(hashes[seed][a]==hashes[seed][b]){printf(" %d:%d(p%u),%d(p%u)",seed,a,(unsigned)pres[seed][a],b,(unsigned)pres[seed][b]);++printed;}
    puts(""); free(frame.pixels); return 0;
}
