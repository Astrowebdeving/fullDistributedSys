#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <errno.h>

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <error_time_in_seconds_with_nanoseconds>\n", argv[0]);
        return 1;
    }


    double error_time = atof(argv[1]);


    if (error_time < 0) {
        printf("Stopping system time for %.9f seconds...\n", -error_time);
        sleep((unsigned int)(-error_time));  // Sleep for the absolute value of error_time in seconds
        return 0;
    }


    struct timespec current_time;
    if (clock_gettime(CLOCK_REALTIME, &current_time) != 0) {
        perror("Error getting current time");
        return errno;
    }

 
    time_t seconds_to_add = (time_t)error_time;
    long nanoseconds_to_add = (long)((error_time - seconds_to_add) * 1e9);


    current_time.tv_sec += seconds_to_add;

    current_time.tv_nsec += nanoseconds_to_add;
    if (current_time.tv_nsec >= 1e9) {
        current_time.tv_sec += 1;
        current_time.tv_nsec -= 1e9;
    }

    // Set the new system time
    if (clock_settime(CLOCK_REALTIME, &current_time) != 0) {
        perror("Error setting time");
        return errno;
    }

    printf("System time adjusted by %.9f seconds.\n", error_time);
    return 0;
}
