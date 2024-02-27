#!/bin/python3

import os
import sys
import datetime

utsstart = datetime.datetime(year=1980, month=1, day=1)

def interpretType(type):
    if type == 0:
        return "Weekday"
    elif type == 1:
        return "BST Start"
    elif type == 2:
        return "BST End"
    elif type == 3:
        return "Bank Holiday"
    else:
        raise Exception("Invalid type value {}".format(type))

def interpretFile(fname, isNewFormat):
    print(fname)
    print('---------------------')
    print('')
    try:
        with open(fname, "rb") as fh:
            for i in range(16):
                if isNewFormat:
                    utsdate = int.from_bytes(fh.read(2), 'little')
                    type = int.from_bytes(fh.read(1), 'little')
                else:
                    entry = int.from_bytes(fh.read(2), 'little')
                    utsdate = entry & 0x3FFF
                    type = (entry >> 14) & 0x03
                date = utsstart + datetime.timedelta(days=utsdate)
                print("{} {}".format(date.strftime("%a %Y-%m-%d"), interpretType(type)))
    except Exception as e:
        print(e, file=sys.stderr)
    print('')

if len(sys.argv) < 2:
    raise Exception('No files specified!')

for fname in sys.argv[1:]:
    fsize = os.path.getsize(fname)
    if fsize == 32:
        interpretFile(fname, False)
    elif fsize == 48:
        interpretFile(fname, True)
    else:
        raise Exception("{} not a Special Days Table".format(fname))
