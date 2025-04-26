#ifndef __UART_FILE_H___
#define __UART_FILE_H___

#include <stdio.h>

#include "sim_irq.h"
#include "sim.h"

enum {
	IRQ_UART_FILE_BYTE_IN = 0,
};

typedef struct uart_t {
	char *buff;
	uint32_t size;
	uint32_t idx;
    
    avr_irq_t *	irq;		// irq list
} uart_t;

void uart_init(struct avr_t *avr, uart_t *p, uint32_t size, char *buffer);

sim_return uart_attach(struct avr_t *avr, uart_t *p, char uart);

void uart_cleanup(uart_t *p);

#endif