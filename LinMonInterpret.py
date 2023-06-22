#!/bin/python3

import sys
import struct
import xlrd

def readPacket(fh):
    src = str(fh.read(5))
    ts = xlrd.xldate_as_datetime(struct.unpack('d', fh.read(8))[0], 0)
    len = int.from_bytes(fh.read(4), 'little')
    data = fh.read(len)
    return (src, ts, data)

def interpretFile(fname):
    print(fname)
    print('---------------------')
    print('')
    with open(fname, "rb") as fh:
        while True:
            (src, ts, data) = readPacket(fh)
            print("{} {}: {}".format(src, ts, data.hex()))
    print('')

if len(sys.argv) < 2:
    raise Exception('No files specified!')

for fname in sys.argv[1:]:
    interpretFile(fname)
