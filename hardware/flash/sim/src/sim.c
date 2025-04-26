#include <stdio.h>
#include <dirent.h> 
#include <string.h>
#include <stdlib.h>

#include "sim_elf.h"
#include "avr_twi.h"

#include "utils.h"
#include "sim.h"
#include "custom_i2c_eeprom.h"
#include "uart.h"


sim_return run_sim(char *firmware_path, char *eeprom_path, uint32_t uart_size, char* uart_buff, uint32_t* uart_bytes_read){
    // load firmware
    elf_firmware_t firmware = {{0}};
    
    int ret = elf_read_firmware(firmware_path, &firmware);
    if(ret != 0){
        fputs("failed to load firmware\n", stderr);
        return ERROR;
    }
 
    strcpy(firmware.mmcu, MCU);
    firmware.frequency = FREQ;
 
    // Create mcu
    avr_t *mcu;
    mcu = avr_make_mcu_by_name(MCU);
    if(mcu == NULL) {
        fputs("failed to make MCU\n", stderr);
        return ERROR;
    }
    ret = avr_init(mcu);
    if(ret != 0){
        fputs("failed to initialize MCU\n", stderr);
        return ERROR;
    }
    avr_load_firmware(mcu, &firmware);

    // Create eeprom
    i2c_eeprom_t eeprom;
    sim_return perf_ret = i2c_eeprom_init_file(mcu, &eeprom, EEPROM_ADDR, 0x01, eeprom_path);
    if(perf_ret != SUCCESS){
        fputs("failed to initialize EEPROM\n", stderr);
        return perf_ret;
    }
    i2c_eeprom_attach(mcu, &eeprom, AVR_IOCTL_TWI_GETIRQ(0));
    
    // Create uart
    uart_t uart;
    uart_init(mcu, &uart, uart_size, uart_buff);
    perf_ret = uart_attach(mcu, &uart, '0');
    if(perf_ret != SUCCESS){
        fputs("failed to attach to uart\n", stderr);
        return perf_ret;
    }

    // Run sim
    mcu->state = cpu_Running;
    int state = cpu_Running;
    while ((state != cpu_Done) && (state != cpu_Crashed) && (get_time(mcu) < TIMEOUT)){
        state = avr_run(mcu);
    }

    if(uart_bytes_read != NULL)
        *uart_bytes_read = uart.idx;

    i2c_eeprom_cleanup(&eeprom);
    uart_cleanup(&uart);
    free(mcu);
    
    return mcu->state == cpu_Crashed ? RUN_ERROR : SUCCESS;
}