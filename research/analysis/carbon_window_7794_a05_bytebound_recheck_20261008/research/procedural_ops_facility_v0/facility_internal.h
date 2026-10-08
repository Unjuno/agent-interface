#ifndef PROCEDURAL_OPS_FACILITY_INTERNAL_H
#define PROCEDURAL_OPS_FACILITY_INTERNAL_H
#include "facility.h"

double fac_clampd(double v, double lo, double hi);
int fac_imax(int a, int b);
int fac_imin(int a, int b);
double fac_rng_unit(Facility *f);
int fac_rng_int(Facility *f, int n);
void fac_hash_event(Facility *f, uint64_t tag, int a, int b);
uint64_t fac_fnv_bytes(uint64_t h, const void *data, size_t n);
void fac_schedule_watcher(Facility *f, int i);
int fac_watcher_interval(Facility *f);
double fac_wrap_angle(double a);
void fac_apply_movement(Facility *f, const FacilityInput *in);

#endif
