#include <math.h>

#include "utils.h"

size_t get_file_size(
        FILE *file)
{
    fseek(file, 0, SEEK_END); // seek to end of file
    size_t size = (size_t) ftell(file); // get current file pointer
    fseek(file, 0, SEEK_SET); // seek back to beginning of file
    
    return size;
}