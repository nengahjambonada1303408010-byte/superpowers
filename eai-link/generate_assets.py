"""Generates placeholder PNG assets for EAi Link Expo app."""
import struct
import zlib
import os

def make_png(width, height, bg_color, text_color=(255, 255, 255)):
    """Create a solid-color PNG with width x height dimensions."""
    r, g, b = bg_color

    # Build raw image data: each row starts with filter byte 0 (None)
    raw_rows = []
    row = bytes([0])  # filter byte
    for _ in range(width):
        row += bytes([r, g, b])
    raw_rows = row * height

    compressed = zlib.compress(raw_rows)

    def chunk(name, data):
        c = name + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr = chunk(b'IHDR', ihdr_data)
    idat = chunk(b'IDAT', compressed)
    iend = chunk(b'IEND', b'')

    return sig + ihdr + idat + iend


assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
os.makedirs(assets_dir, exist_ok=True)

# Dark navy background matching app.json backgroundColor
BG = (15, 23, 42)   # #0f172a
ACCENT = (59, 130, 246)  # #3b82f6

# icon.png — 1024x1024
with open(os.path.join(assets_dir, 'icon.png'), 'wb') as f:
    f.write(make_png(1024, 1024, BG))

# adaptive-icon.png — 1024x1024
with open(os.path.join(assets_dir, 'adaptive-icon.png'), 'wb') as f:
    f.write(make_png(1024, 1024, ACCENT))

# splash.png — 1284x2778
with open(os.path.join(assets_dir, 'splash.png'), 'wb') as f:
    f.write(make_png(1284, 2778, BG))

print("Assets generated:")
for name in ['icon.png', 'adaptive-icon.png', 'splash.png']:
    path = os.path.join(assets_dir, name)
    print(f"  {name}: {os.path.getsize(path):,} bytes")
