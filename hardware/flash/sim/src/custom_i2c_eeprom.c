/*
	i2c_eeprom.c

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


#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "sim_avr.h"
#include "avr_twi.h"
#include "utils.h"

#include "custom_i2c_eeprom.h"

/*
 * called when a RESET signal is sent
 */
static void
i2c_eeprom_in_hook(
		struct avr_irq_t * irq,
		uint32_t value,
		void * param)
{
	i2c_eeprom_t * p = (i2c_eeprom_t*)param;
	avr_twi_msg_irq_t v;
	v.u.v = value;

	/*
	 * If we receive a STOP, check it was meant to us, and reset the transaction
	 */
	if (v.u.twi.msg & TWI_COND_STOP) {
		if (p->selected) {
			// it was us !
			if (p->verbose)
				fprintf(stderr, "eeprom received stop\n");
		}
		i2c_eeprom_reset(p);
	}
	/*
	 * if we receive a start, reset status, check if the slave address is
	 * meant to be us, and if so reply with an ACK bit
	 */
	if (v.u.twi.msg & TWI_COND_START) {
		p->selected = 0;
		p->index = 0;
		if ((p->addr_base & ~p->addr_mask) == (v.u.twi.addr & ~p->addr_mask)) {
			// it's us !
			if (p->verbose)
				fprintf(stderr, "eeprom received start\n");
			p->selected = v.u.twi.addr;
			avr_raise_irq(p->irq + TWI_IRQ_INPUT,
					avr_twi_irq_msg(TWI_COND_ACK, p->selected, 1));
		}
	}
	/*
	 * If it's a data transaction, first check it is meant to be us (we
	 * received the correct address and are selected)
	 */
	if (p->selected) {
		/*
		 * This is a write transaction, first receive as many address bytes
		 * as we need, then set the address register, then start
		 * writing data,
		 */
		if (v.u.twi.msg & TWI_COND_WRITE) {
			// address size is how many bytes we use for address register
			avr_raise_irq(p->irq + TWI_IRQ_INPUT,
					avr_twi_irq_msg(TWI_COND_ACK, p->selected, 1));
			if (p->index < p->addr_size) {
				p->reg_addr |= (v.u.twi.data << (p->index * 8));
				if (p->index == p->addr_size-1) {
					// add the slave address, if relevant
					// p->reg_addr += ((p->selected & 1) - p->addr_base) << 7;
					if (p->verbose)
						fprintf(stderr, "eeprom set address to 0x%x\n", p->reg_addr);
				}
			} else {
				if (p->verbose)
					fprintf(stderr, "eeprom WRITE data 0x%x: %02x\n", p->reg_addr, v.u.twi.data);
				p->ee[p->reg_addr++] = v.u.twi.data;
			}
			if(p->reg_addr >= p->size) p->reg_addr = p->size - 1;
			p->index++;
		}
		/*
		 * It's a read transaction, just send the next byte back to the master
		 */
		if (v.u.twi.msg & TWI_COND_READ) {
			if (p->verbose)
				fprintf(stderr, "eeprom READ data 0x%x: %02x\n", p->reg_addr, p->ee[p->reg_addr]);
			uint8_t data = p->ee[p->reg_addr++];
			avr_raise_irq(p->irq + TWI_IRQ_INPUT,
					avr_twi_irq_msg(TWI_COND_READ, p->selected, data));
			if(p->reg_addr >= p->size) p->reg_addr = p->size - 1;
			p->index++;
		}
	}
}

static const char * _ee_irq_names[2] = {
		[TWI_IRQ_INPUT] = "8>eeprom.out",
		[TWI_IRQ_OUTPUT] = "32<eeprom.in",
};

sim_return
i2c_eeprom_init(
		struct avr_t * avr,
		i2c_eeprom_t * p,
		uint8_t addr,
		uint8_t mask,
		size_t size,
		uint8_t *data)
{
	memset(p, 0, sizeof(*p));

	p->ee=malloc(size);
	if(p->ee==NULL){
		fprintf(stderr, "eeprom ERROR: Failed to allocate memory. Failed to Init.\n");
		return ERROR;
	}
	memset(p->ee, 0xFF, size);
	if(data)
		memcpy(p->ee, data, size);

	p->addr_base = addr;
	p->addr_mask = mask;

	p->irq = avr_alloc_irq(&avr->irq_pool, 0, 2, _ee_irq_names);
		
	avr_irq_register_notify(p->irq + TWI_IRQ_OUTPUT, i2c_eeprom_in_hook, p);
	p->size = size;
	p->addr_size= size > 255 ? 2 : 1;

	return SUCCESS;
}

sim_return
i2c_eeprom_init_file(
		struct avr_t * avr,
		i2c_eeprom_t * p,
		uint8_t addr,
		uint8_t mask,
		char *path)
{
	FILE *file = fopen(path, "rb");
    if(file == NULL){
        fprintf(stderr, "eeprom ERROR: Failed to open eeprom data file.\n");
		return ERROR;
	}

	size_t size = get_file_size(file);
	uint8_t ret = i2c_eeprom_init(avr, p, addr, mask, size, NULL);
	if(ret != SUCCESS)
		return ret;

	size_t elms = fread(p->ee, size, 1, file);
	if(!elms){
		fprintf(stderr, "eeprom ERROR: Unable to copy file data to eeprom.\n");
		return ERROR;
	}

	fclose(file);
	return SUCCESS;
}

void
i2c_eeprom_attach(
		struct avr_t * avr,
		i2c_eeprom_t * p,
		uint32_t i2c_irq_base )
{
	// "connect" the IRQs of the eeprom to the TWI/i2c master of the AVR
	avr_connect_irq(
		p->irq + TWI_IRQ_INPUT,
		avr_io_getirq(avr, i2c_irq_base, TWI_IRQ_INPUT));
	avr_connect_irq(
		avr_io_getirq(avr, i2c_irq_base, TWI_IRQ_OUTPUT),
		p->irq + TWI_IRQ_OUTPUT );
}

void
i2c_eeprom_reset(
	i2c_eeprom_t *p )
{
	p->selected=0;
	p->reg_addr=0;
	p->index = 0;
}

void
i2c_eeprom_cleanup(
		i2c_eeprom_t *p)
{
	if(p->ee){
		free(p->ee);
		p->ee=NULL;
	}
	if(p->irq){
		avr_free_irq(p->irq, 2);
		p->irq = NULL;
	}
}