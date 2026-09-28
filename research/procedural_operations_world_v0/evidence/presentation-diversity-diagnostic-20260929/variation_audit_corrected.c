#include "../../ops_world.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static uint64_t hash_pixels(const uint32_t *p, size_t n, int stride_only) {
    uint64_t h=1469598103934665603ULL;
    for(size_t i=0;i<n;i+=(stride_only?97:1)){h^=p[i];h*=1099511628211ULL;}
    return h;
}

static uint64_t render_hash(uint64_t seed, uint64_t family, const OwDifficulty *d,
                            OwFrame *frame, int stride_only, uint8_t *actual) {
    enum { PIXELS=OW_WIDTH*OW_HEIGHT };
    OwWorld w; ow_init_with_family(&w,seed,family,d);
    w.task_mask=OW_TASK_TARGET; w.task_deps[2]=0; w.target_complete=0;
    w.objects[w.target_object].active=1; *actual=w.presentation_family;
    ow_render(&w,frame);
    return hash_pixels(frame->pixels,PIXELS,stride_only);
}

int main(void) {
    enum { SEEDS=256, FAMILIES=20, SAMPLE_SEED=234, PIXELS=OW_WIDTH*OW_HEIGHT };
    OwDifficulty d; ow_default_difficulty(&d);
    d.watcher_count=64; d.dependency_depth=0;
    OwFrame frame; frame.pixels=calloc(PIXELS,sizeof(uint32_t));
    if(!frame.pixels) return 2;
    uint64_t hashes[SEEDS][FAMILIES]; uint8_t pres[SEEDS][FAMILIES];
    unsigned family_mask=0,cue_modes=0; size_t collisions=0,aliases=0;
    size_t stride_collisions=0,stride_pairs=0,full_duplicates=0;
    for(uint64_t seed=0;seed<SEEDS;++seed) for(uint64_t fk=0;fk<FAMILIES;++fk){
        hashes[seed][fk]=render_hash(seed,fk,&d,&frame,0,&pres[seed][fk]);
        cue_modes|=1u<<(pres[seed][fk]%4); family_mask|=1u<<(pres[seed][fk]%12);
        for(uint64_t prior=0;prior<fk;++prior) if(hashes[seed][prior]==hashes[seed][fk]){
            if(pres[seed][prior]==pres[seed][fk]) ++aliases; else ++collisions;
        }
    }
    for(uint64_t fk=0;fk<FAMILIES;++fk) for(uint64_t prior=0;prior<fk;++prior){
        uint8_t current_family,prior_family;
        uint64_t current=render_hash(SAMPLE_SEED,fk,&d,&frame,1,&current_family);
        uint64_t previous=render_hash(SAMPLE_SEED,prior,&d,&frame,1,&prior_family);
        if(current_family!=prior_family){ ++stride_pairs; if(current==previous) ++stride_collisions; }
        if(hashes[SAMPLE_SEED][fk]==hashes[SAMPLE_SEED][prior]) ++full_duplicates;
    }
    printf("schema=opsworld-presentation-full-frame-audit-corrected-v1\nseeds=%d\nfamilies_per_seed=%d\ncombinations=%d\nfamily_mask=0x%03x\ncue_mode_mask=0x%x\ndistinct_presentation_full_frame_collisions=%zu\nsame_presentation_key_aliases=%zu\n",SEEDS,FAMILIES,SEEDS*FAMILIES,family_mask,cue_modes,collisions,aliases);
    printf("sample_seed=%d\nsample_seed_distinct_full_frame_hashes=%zu\nsample_seed_duplicate_full_frame_pairs=%zu\nsample_seed_stride97_distinct_family_pairs=%zu\nsample_seed_stride97_colliding_distinct_family_pairs=%zu\n",SAMPLE_SEED,FAMILIES-full_duplicates,full_duplicates,stride_pairs,stride_collisions);
    free(frame.pixels); return 0;
}
