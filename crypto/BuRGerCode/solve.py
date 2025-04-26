flag_format = "UMASS{"
enc = "60797d6e6c455d490d41774a1b4e1d705e1c155314557d415452075211573957033b0459015e5b16" 
for offset in range(256):
    decrypted = bytearray()
    for i in range(0, len(enc), 2):
        hex_byte = enc[i:i+2]
        byte = int(hex_byte, 16)
        gray_code = byte ^ (i // 2 + offset) ^ ((i // 2 + offset) >> 1)
        decrypted.append(gray_code & 0xFF)
    decrypted_str = decrypted.decode("ascii", errors="ignore")
    if decrypted_str.startswith(flag_format):
        print(decrypted_str)
        break
