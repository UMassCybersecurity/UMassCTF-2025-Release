#ifndef __SIM_H
#define __SIM_H

#define MCU "atmega328p"
#define FREQ 16000000

#define TIMEOUT 5

#define EEPROM_ADDR 0b10101000

typedef enum sim_return{
    SUCCESS,
    ERROR,
    RUN_ERROR,
} sim_return;

/*
 * Runs an AVR simulation using the specified data.
 */
sim_return run_sim(char *firmware_path, char *eeprom_path, uint32_t uart_size, char* uart_buff, uint32_t* uart_bytes_read);

#endif