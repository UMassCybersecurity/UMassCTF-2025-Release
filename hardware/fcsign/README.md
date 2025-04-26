# FCSIGN
Author: RS311

Description: What's up homie, it's Brody. I got one of those decomissioned signs from a motivational facility for something called UMassCTF. You think there's anything cool in here? Got it hooked up in my lab if you want to mess around with it...

Flag: `UMASS{un(_b3_w1l1n_w1th_s1d3ch4nn3l1n_XT60WWSC}`

## Intended Solution(s)

### Talking to the Chip
- The first step is to communicate with the chip. The user needs to emulate a proper transaction with the UK47XD, which requires following the datasheet provided. In other words, the user needs to send the following packets (which should follow the format specified in the datasheet):

```Python
    # Put us into debug mode. The chip will ignore you otherwise.
    await send_data(socket, b'\x55\x00\xC1\x00')
    data, cycles = await receive_data(socket)
```

```Python
    # Initialize communications. The chip will return a flow error otherwise.
    await send_data(socket, b'\x33\x01\x00\x03')
    data, cycles = await receive_data(socket)
```

```Python
    # Set the frequency. This can be either 8 MHz or 16 MHz. The chip will return a flow error otherwise.
    await send_data(socket, b'\x33\x05\x00\x05\x00\x12\x7A\x00')
    data, cycles = await receive_data(socket)
```

### Getting the Password
After communicating with the chip, the user then needs to unlock the chip with a password. **The password is randomly generated on every connection attempt**. Of course, the password is not provided, since that would be too easy.

Bruteforcing will **not** work! The user only gets 26 * 16 + 15 attempts before the chip is burned as a security feature. In the worst case, bruteforcing would give you 26^16 attempts to go through, which is approximately 4 * 10^22 attempts. Furthermore, you cannot do a smart bruteforce, because the password is also reset every connection attempt. 

Therefore, in lieu being able to ask someone for the password, user needs to extract the password from the chip using a sidechannel attack on the cycle count. The password check is done as a byte-by-byte comparison, where the result of the byte comparison is used to stop execution of the chip. The key is to pay attention to the difference in cycles between each password attempt. 
- If the difference between the two observed cycles is 250, then the numerical value of the byte is less than that of the one stored on the chip. 
- If the difference between the two observed cycles is 500, then the numerical value of the byte is greater than that of the one stored on the chip.
- If the difference between the two observed cycles is 1000 **or greater**, then the numerical value of the byte is equal to that of the one stored on the chip. **However, this means that if you get this character correct, you need to take this into account when looking at the cycles for the following characters.**

That being said, you need to keep your attempts under 26 * 16 + 15 attempts. Here's how you make it at most 26 * 16 + 15. Because you have three distinct states (lower than, equal to, higher than) for the character cycle sidechannel, and because the alphabet is contiguously placed next to each other (meaning [ord(A), ord(Z)] exists), you can use the sidechannel to inform a binary search algorithm.

So, what you can do is the following to leak the password:
```Python
    # Leak the password.
    leaked = False
    id_bytes = [ord('A') for index in range(16)]
    test_point = 0
    char_attempt = 0
    previous_cycle_count = cycles
    low, mid, high = ord('A'), 0, ord('Z')
    cycle_correction_base = 0
    while not leaked:
        # We're good.
        if test_point >= 16:
            leaked = True
            continue

        mid = low + (high - low) // 2
        # print(f'midpoint is {mid}')
        print(f'as character, {chr(mid)}')
        id_bytes[test_point] = mid
        char_attempt += 1

        # Send our current password, get information back.
        await send_data(socket, b'\x33\x11\x00\x34' + bytes(id_bytes))
        data, cycles = await receive_data(socket)
        print(f'Got back {cycles}')

        # There's three thresholds that will help us do a binary search.
        # Byte is < correct one: ~250 cycles.
        # Byte is > correct one: ~500 cycles.
        # Byte is = correct one: >= ~1000 cycles.
        cycle_difference = cycles - previous_cycle_count - cycle_correction_base
        previous_cycle_count = cycles

        # If the cycle difference is close to 250 (within 4 to 6 cycles), less than.
        if 250 <= cycle_difference <= 256:
            low = mid + 1
            continue

        # If close to 500, greater than.
        elif 500 <= cycle_difference <= 506:
            high = mid - 1 
            continue

        # If close to 1000, equal
        else:
            print(f'Character at point {test_point} is {chr(id_bytes[test_point])}; took {char_attempt} tries')
            test_point += 1
            # Reset search params
            low, high = ord('A'), ord('Z')
            char_attempt = 0
            cycle_correction_base += 1000

    print(f'Password is {bytes(id_bytes)}')
```

If done correctly, this will get you the password almost all of the time, unless there is some case where binary search fails.

### Reading the Flash and Getting the Flag
After the user is authenticated, you can freely read from the chip using the read command, as follows:

```Python
address = 0
with open('solve_dump.bin', 'wb') as OUT:
    while address < 0xEDC00:
        await send_data(socket, b'\x33\x05\x00\x69' + struct.pack('<I', address))
        data, cycles = await receive_data(socket)
        OUT.write(data[5:])
        address += 0x400
```

With the firmware dumped, the user can now perform analysis on the contents of the file. Using `binwalk`, the user can extract the files from the firmware image:
```sh
[s1matic@swagbook ~/Documents/umassctf-25/lcsign/src] $ binwalk -e solve_dump.bin 

/home/s1matic/Documents/umassctf-25/lcsign/src/extractions/solve_dump.bin
-----------------------------------------------------------
DECIMAL                            HEXADECIMAL                        DESCRIPTION
-----------------------------------------------------------
881                                0x371                              POSIX tar archive, file count: 6
-----------------------------------------------------------
[+] Extraction of tarball data at offset 0x371 completed successfully
-----------------------------------------------------------

Analyzed 1 file for 85 file signatures (187 magic patterns) in 11.0 milliseconds
```

This will yield a set a files, containing dev code and frames for the sign. Looking at `frame_2.png` in `frame.xz` will give you the flag.

