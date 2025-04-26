/*
 * gcc main.c -o ../assets/calc -T wild.lds -Wl,--dynamic-linker=./ld-linux-x86-64.so.2 -Wl,-rpath ./
 */

#include <pthread.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdio.h>

#define DATA_SIZE 8

uint8_t global_data[DATA_SIZE];

void *process(void* data){
    // generate local data
    uint8_t val = (*(uint8_t*)data)++;
    srand(val);
    uint8_t local_data[DATA_SIZE];
    for(int i = 0; i < DATA_SIZE; i++){
        local_data[i] = (uint8_t) rand();
    }

    // process data
    printf("Processing: %hhx ^ %hhx = %hhx\n", global_data[val], local_data[val], global_data[val] ^ local_data[val]);
    if(*(uint8_t *)data == DATA_SIZE){
        *(uint8_t *)data = 0;
    }
}

uint8_t get_number(uint8_t *data){
    char buff[32];
    if(fgets(buff, sizeof(buff), stdin) == NULL)
        return 1;
    

    buff[strlen(buff)-1] = 0;
    if(strcmp(buff, "q") == 0)
        return 2;
    if(sscanf(buff, "%hhx", data) != 1) {
        puts("Invalid input!");
        return 1;
    }
    return 0;
}

uint8_t get_feedback(char *buff){
    printf("Would you like to give feedback(y/N): ");
    
    if(fgets(buff, 0x100, stdin) == NULL)
        return 0;
        
    buff[strlen(buff)-1] = 0;
    if(strcmp(buff, "y") && strcmp(buff, "yes"))
        return 0;

    if(fgets(buff, 0x100, stdin) == NULL)
        return 0;

    return 1;
}

int main() {
    setbuf(stdout, NULL);
    
    uint8_t data_idx = 0;

    puts("Welcome to the parallel processing unit (PPU)!");
    
    while(1){
        // get global data
        puts("Enter global data (q to finish)");
        
        uint8_t resp;
        uint8_t data;
        uint8_t idx=0;

        while((resp = get_number(&data)) != 2) {
            if(resp != 0)
                continue;
            
            global_data[idx++]=data;
        }

        puts("Enter number of threads (q to quit)");
        while((resp = get_number(&data)) == 1) {}
        if(resp == 2) {
            break;
        }

        pthread_t thread[data];
        // do the processing
        for(int i = 0; i < data; i++) {
            if(pthread_create(thread+i, NULL, process, &data_idx) != 0)
                return 1;
        }
        for(int i = 0; i < data; i++) {
            if(pthread_join(thread[i], NULL) != 0)
                return 1;
        }
    }

    // get feedback
    int sfd = socket(AF_INET, SOCK_DGRAM, 0);
        if (sfd == -1) 
            return 1;

    struct sockaddr_in servaddr;
    bzero(&servaddr,sizeof(servaddr));
    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = inet_addr("127.0.0.1");
    servaddr.sin_port = htons(9000);

    struct resp_data {
        char buff[100]; 
        char *msg;
    };
    struct resp_data resp = {.msg = "Sending feedback..."};

    while(get_feedback(resp.buff)){
        puts(resp.msg);
        sendto(sfd, resp.buff, 100, 0, (struct sockaddr *)&servaddr, sizeof(servaddr));
    }
}