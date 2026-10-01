#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <setjmp.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <time.h>

static sigjmp_buf trap;
static void on_sigill(int sig) { (void)sig; siglongjmp(trap, 1); }
static inline uint64_t read_cntvct(void) { uint64_t x; __asm__ volatile("isb; mrs %0, cntvct_el0" : "=r"(x)); return x; }
static inline uint64_t read_cntfrq(void) { uint64_t x; __asm__ volatile("mrs %0, cntfrq_el0" : "=r"(x)); return x; }
static inline uint32_t read_pmccntr(void) { uint64_t x; __asm__ volatile("isb; mrs %0, pmccntr_el0" : "=r"(x)); return (uint32_t)x; }
static uint64_t ns(struct timespec t) { return (uint64_t)t.tv_sec*1000000000ULL+(uint64_t)t.tv_nsec; }
int main(void) {
    struct sigaction sa={0}; sa.sa_handler=on_sigill; sigemptyset(&sa.sa_mask); sigaction(SIGILL,&sa,0);
    uint64_t fq=read_cntfrq(); printf("CNTFRQ_EL0=%llu\n",(unsigned long long)fq);
    for(int i=0;i<5;i++) {
        struct timespec a,b,req={0,100000000}; uint32_t p0,p1; uint64_t c0,c1;
        if(sigsetjmp(trap,1)) { printf("sample=%d status=SIGILL_PMU_READ\n",i); return 0; }
        clock_gettime(CLOCK_MONOTONIC,&a); c0=read_cntvct(); p0=read_pmccntr();
        while(clock_nanosleep(CLOCK_MONOTONIC,0,&req,&req)==EINTR) {}
        p1=read_pmccntr(); c1=read_cntvct(); clock_gettime(CLOCK_MONOTONIC,&b);
        printf("sample=%d status=ok monotonic_ns=%llu cntvct_delta=%llu pmccntr_delta=%u\n",i,
          (unsigned long long)(ns(b)-ns(a)),(unsigned long long)(c1-c0),(uint32_t)(p1-p0));
    }
    return 0;
}
