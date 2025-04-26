#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdint.h>

#include "sim.h"

#define MAX_SIZE 64 * 1024

#define clean_exit(num) fclose(file); remove(template); exit(num);

int main(int argc, char **argv){
    if(argc != 2){
        fprintf(stderr, "Usage: %s EEPROM_PATH\n", argv[0]);
        exit(-1);
    }

    setbuf(stdout, NULL);

    // make tmp file
    char template[] = "firmware_XXXXXX";
    int fd = mkstemp(template);

    if(fd == -1){
        fputs("failed to create temp file\n", stderr);
        return -1;
    }

    FILE* file = fdopen(fd, "w");
    if(file == NULL) {
        perror("failed to open temp file");
        clean_exit(-1)
    }
    

    unsigned int firmware_size;
    if(!fread(&firmware_size, 4, 1, stdin)){
        fputs("unable to get firmware size\n", stderr);
        close(fd);
        remove(template);
        exit(-1);
    }
    
    if(firmware_size > MAX_SIZE){
        fputs("firmware to large\n", stderr);
        clean_exit(-1)
    }
    
    char buff[4096];
    while(1){
        if (!fread(buff, firmware_size < 4096 ? firmware_size : 4096, 1, stdin)) {
            perror("read firmware");
            clean_exit(-1)
        }
        if (!fwrite(buff, firmware_size < 4096 ? firmware_size : 4096, 1, file)){
            perror("write firmware");
            clean_exit(-1)
        }
        if(firmware_size < 4096)
            break;
        firmware_size -= 4096;
    }

    fputc(0, stdout);

    uint32_t uart_size = 0;
    sim_return ret = run_sim(template, argv[1], 4096, buff, &uart_size);

    fputc(ret, stdout);
    fwrite(&uart_size, sizeof(uart_size), 1, stdout);
    fwrite(buff, uart_size, 1, stdout);

    if(ret == ERROR){
        clean_exit(-1)
    }

    clean_exit(0)
}