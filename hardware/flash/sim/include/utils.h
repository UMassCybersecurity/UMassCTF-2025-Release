#ifndef __UTILS_H___
#define __UTILS_H___

#include <stdio.h>

#include "sim_avr.h"

/*
 * Returns the time the avr simulation has been running.
 * This is calculated using clock cycles and frequency
 */
static inline double get_time(struct avr_t *avr) {
    return (double)avr->cycle/avr->frequency;
}

/*
 * Gets the file size (in bytes).
 * @note this will reset the file to the beginning 
 */
size_t get_file_size(
    FILE *size);

#endif