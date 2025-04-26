/*
    Code for the UMASS CTF SIGN - Developer Only
    THIS SHOULD NOT BE IN CONSUMER PRODUCT!
    Copyright © 2025 FCSign
*/

#include <stdio.h>
#include <stdlib.h>

#define FRAME_WIDTH 500
#define FRAME_HEIGHT 500
#define FRAME_CNT 3

struct Frame {
    // Each frame = 640x480! This was the only display we had on hand
    char data[FRAME_WIDTH*FRAME_HEIGHT];
};

int main() {
    // In Loop, Read all Frames from FRAME.TAR!
    // Assume ALREADY extracted.
    int frame_no = 0;
    while (1) {
        char NAME[0x300];
        char DATA_BUFFER[FRAME_HEIGHT * FRAME_WIDTH + 1];
        //TODO: Figure out memset. What does it do?
        snprintf(NAME, 0x29F, "frame_%d.png", frame_no);
        printf("LOADING FRAME %d", frame_no);
        
        FILE *f = fopen(NAME, "rb");
        fread(DATA_BUFFER, sizeof(char), FRAME_HEIGHT * FRAME_WIDTH, f);

        frame_no = (frame_no + 1) % FRAME_CNT;
        //TODO: FIGURE OUT CLOCKING TO SCREEN! NEED LATCH!
    }
    return 0;
}