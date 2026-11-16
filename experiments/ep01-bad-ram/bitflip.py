"""Small demonstrations used in episode 1. Run: python3 bitflip.py"""
import struct

def flip(text, index, bit):
    b = bytearray(text.encode())
    b[index] ^= 1 << bit
    return b.decode()

print(flip("PAY 100", 4, 3))                       # one bit in '1' (0x31) gives '9' (0x39)
print(hex(0x00007ffd1c2a4e10 ^ (1 << 5)))          # one bit in a pointer moves it 32 bytes
print(struct.pack("<Q", 0x7a6c7258554e494c))       # pattern 17 in memory order on a little-endian CPU
