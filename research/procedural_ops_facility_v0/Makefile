CC ?= cc
CFLAGS ?= -O3 -std=c11 -Wall -Wextra -Wpedantic
LDLIBS ?= -lm -lX11
CORE_OBJS = facility_world.o facility_tasks.o facility_render.o facility_misc.o

all: facility core_tests

facility: $(CORE_OBJS) main.o
	$(CC) $(CFLAGS) -o $@ $^ $(LDLIBS)

core_tests: $(CORE_OBJS) core_tests.o
	$(CC) $(CFLAGS) -o $@ $^ -lm

facility_world.o: facility_world.c facility.h facility_internal.h
	$(CC) $(CFLAGS) -c facility_world.c

facility_tasks.o: facility_tasks.c facility.h facility_internal.h
	$(CC) $(CFLAGS) -c facility_tasks.c

facility_render.o: facility_render.c facility.h
	$(CC) $(CFLAGS) -c facility_render.c

facility_misc.o: facility_misc.c facility.h
	$(CC) $(CFLAGS) -c facility_misc.c

main.o: main.c facility.h
	$(CC) $(CFLAGS) -c main.c

core_tests.o: core_tests.c facility.h
	$(CC) $(CFLAGS) -c core_tests.c

clean:
	rm -f facility core_tests *.o

.PHONY: all clean
