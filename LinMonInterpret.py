#!/bin/python3

import sys
import struct
import xlrd

def findFirstPacket(fh):
    data = fh.read(100)
    pos = data.find(b'COM')
    if pos < 0:
        raise Exception('Could not find COM in first 100 bytes')
    fh.seek(pos)

def readPacket(fh):
    src = fh.read(5).decode("ascii")
    ts = xlrd.xldate_as_datetime(struct.unpack('d', fh.read(8))[0], 0)
    len = int.from_bytes(fh.read(4), 'little')
    data = fh.read(len)
    return (src, ts, data)

def interpretFile(fname):
    print(fname)
    print('---------------------')
    print('')
    try:
        with open(fname, "rb") as fh:
            findFirstPacket(fh)
            while True:
                (src, ts, data) = readPacket(fh)
                print("{} {}: {}".format(src, ts, data.hex()))
    except Exception:
        pass
    print('')

if len(sys.argv) < 2:
    raise Exception('No files specified!')

for fname in sys.argv[1:]:
    interpretFile(fname)
