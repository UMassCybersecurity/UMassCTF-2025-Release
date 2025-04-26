/*
	uart_udp.c

	Copyright 2008, 2009 Michel Pollet <buserror@gmail.com>

 	This file is part of simavr.

	simavr is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	simavr is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with simavr.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <string.h>
#include <stdio.h>
#include <errno.h>
#include <unistd.h>

#include "sim_avr.h"
#include "avr_uart.h"

#include "uart.h"

/*
 * called when a byte is send via the uart on the AVR
 */
static void uart_in_hook(struct avr_irq_t * irq, uint32_t value, void * param)
{
	uart_t *uart = (uart_t *)param;
	if(uart->idx < uart->size)
		uart->buff[uart->idx++] = (char)value;
}

static const char * irq_names[1] = {
	[IRQ_UART_FILE_BYTE_IN] = "8<uart_file.in",
};

void uart_init(struct avr_t * avr, uart_t *p, uint32_t size, char *buff)
{
	p->size = size;
	p->buff = buff;
	p->idx = 0;
	p->irq = avr_alloc_irq(&avr->irq_pool, 0, 1, irq_names);
	avr_irq_register_notify(p->irq + IRQ_UART_FILE_BYTE_IN, uart_in_hook, p);
}

sim_return uart_attach(struct avr_t *avr, uart_t *p, char uart)
{
	// disable the stdio dump, as we are sending binary there
	uint32_t f = 0;
	avr_ioctl(avr, AVR_IOCTL_UART_GET_FLAGS(uart), &f);
	f &= ~AVR_UART_FLAG_STDIO;
	avr_ioctl(avr, AVR_IOCTL_UART_SET_FLAGS(uart), &f);

	avr_irq_t * src = avr_io_getirq(avr, AVR_IOCTL_UART_GETIRQ(uart), UART_IRQ_OUTPUT);

	if (!src) {
        fputs("failed to get uart IRQ\n", stderr);
        return ERROR;
    }

	avr_connect_irq(src, p->irq + IRQ_UART_FILE_BYTE_IN); 
	return SUCCESS;
}

void uart_cleanup(uart_t *p){
	if(p->irq)
		avr_free_irq(p->irq, 1);
}