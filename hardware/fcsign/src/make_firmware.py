import subprocess
import struct
import math
from pathlib import Path

def main():
    # Make the tars.
    subprocess.run(['tar', 'cfv', 'firmware/frames.xz', 'do_not_distribute/frames'])
    subprocess.run(['tar', 'cfv', 'firmware/dev_tools.xz', 'do_not_distribute/dev_tools', 'do_not_distribute/dev_code.c', 'do_not_distribute/README.txt', 'firmware/frames.xz'])

    # Write "rootfs".
    with Path('firmware.bin').open('wb') as final:
        with Path('firmware/base.bin').open('rb') as base:
            data = base.read()
            length = len(data)
            final.write(data)
        
        with Path('firmware/dev_tools.xz').open('rb') as dev_tools:
            data = dev_tools.read()
            length += len(data)
            final.write(data)

        # Alignment
        while int(length / 0x400) != (length / 0x400):
            length += 1
            final.write(b'\x00')

if __name__ == "__main__":
    ret = main()
    exit(ret)