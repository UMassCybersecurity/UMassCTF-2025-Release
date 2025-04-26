from itertools import cycle

lo_offset = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5]
hi_offset = [0, 1, 2, 3, 4, 5, 6, 7]
offset = [((hi << 4) | lo) for hi in hi_offset for lo in lo_offset]
print([hex(x) for x in offset])

def bcd_sub(a: int, b: int):
    # quick hack because i dont have time
    a_ = 100 + int(f'{a:x}')
    b_ = int(f'{b:x}')
    ret = int(f'{a_ - b_}'[-2:], 10)
    print(f'0x{a:x} ({a_ % 100}) - 0x{b:x} ({b_}) -> 0x{ret}')
    return ret

enc = b'\x00\x21\x22\x04\x77\x52\x30\x11\x70\x29\x47\x01\x66\x71\x61\x34\x67\x13\x65\x33\x61\x55\x24\x23\x24\x23\x57\x75\x78\x13\x69\x81\x24\x50\x69\x73\x97\x72\x87\x30\x75\x40\x34\x68\x57\x86\x97\x29\x88\x54\x64\x57\x00\x38\x91'

# reverse the special
dec = [0x30 + bcd_sub(c, o) for c, o in zip(enc, cycle(offset))]

# print(bytes(dec))

