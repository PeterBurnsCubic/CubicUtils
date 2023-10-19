#!/bin/python3

import sys
import struct
import xlrd
import re

PacketStartRx = re.compile(b'COM[12]:')

def skipBadData(fh, e):
    pos = fh.tell()
    data = fh.read(1000)
    dpos = PacketStartRx.search(data)
    dlen = dpos.start() if dpos and dpos.start() > 0 else len(data)
    print("***** bad data at pos {} ({} bytes: {}): {} *****".format(pos, dlen, data[:dlen].hex(), e))
    fh.seek(pos + dlen)

def readPacket(fh):
    src = fh.read(5).decode("ascii")
    ts = xlrd.xldate_as_datetime(struct.unpack('d', fh.read(8))[0], 0)
    dlen = int.from_bytes(fh.read(4), 'little')
    data = fh.read(dlen)
    return (src, ts, data)

def interpretFile(fname):
    print(fname)
    print('---------------------')
    print('')
    try:
        with open(fname, "rb") as fh:
            while fh.read(1):
                fh.seek(-1,1)
                pos = fh.tell()
                try:
                    (src, ts, data) = readPacket(fh)
                    dpos = PacketStartRx.search(data)
                    if dpos is not None:
                        olddlen = len(data)
                        dlen = dpos.start()
                        print("{} {}: {} ({} bytes truncated to {})".format(src, ts, data[:dlen].hex(), olddlen, dlen))
                        fh.seek(pos + 17 + dlen)  # 17 = src (5 bytes), ts (8 bytes) and len (4 bytes)
                        continue
                except Exception as e:
                    fh.seek(pos)
                    skipBadData(fh, e)
                else:
                    print("{} {}: {}".format(src, ts, data.hex()))
    except Exception as e:
        print(e, file=sys.stderr)
    print('')

if len(sys.argv) < 2:
    raise Exception('No files specified!')

for fname in sys.argv[1:]:
    interpretFile(fname)
