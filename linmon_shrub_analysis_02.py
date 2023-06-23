#!/bin/python3

import sys
import os
import struct
import xlrd
import shrub_analysis_02 as sa02

csvA = "CSV_A.csv"
csvB = "CSV_B.csv"

def readLinMonEntry(fh):
    src = fh.read(5).decode("ascii")
    ts = xlrd.xldate_as_datetime(struct.unpack('d', fh.read(8))[0], 0)
    len = int.from_bytes(fh.read(4), 'little')
    data = fh.read(len)
    return (src, ts, data)

def removeShrubTransparency(pdu):
    pdu_ =  pdu.replace(b'\x08\x31', b'\x01') # ESC 1 => SOM
    return pdu_.replace(b'\x08\x32', b'\x08') # ESC 2 => ESC

def calcShrubLRC(data):
    lrc = 0xFF
    for b in data:
        lrc ^= b
    return lrc

def isValidShrubPDU(pdu):
    if len(pdu) > 3:
        if len(pdu) == pdu[2] + 3: # 3rd byte is number of subsequent bytes (incl. LRC)
            if pdu[-1] == calcShrubLRC(pdu[1:-1]):
                return True
            else:
                print("Bad PDU! pdu = {} (last byte = {}) lrc = {}".format(pdu, pdu[-1], calcShrubLRC(pdu[1:-1])))
    elif len(pdu) == 2:
        return pdu[1] == 6 or pdu[1] == 7  # ACK or NAK
    return False

def interpretShrubPDU(pdu):
    if pdu[1] == 6:
        return ('', 'ACK')
    elif pdu[1] == 7:
        return ('', 'NAK')
    else:
        msgtype = pdu[1] & 0xF0 >> 8
        msgseq  = pdu[1] & 0x0F
        return ('{:02x}'.format(pdu[1]), 'Message Type {} Seq {}: {}'.format(msgtype, msgseq, pdu[2:-1]))

def parseShrubFromBuffer(buff, shrub, ts):
    pdu = bytearray()
    for b in buff:
        if b == 1:
            if len(pdu) > 0:
                print('Ignoring invalid data (not SHrUB): {}'.format(pdu))
            pdu = bytearray()
        pdu.append(b)
        pdu_ = removeShrubTransparency(pdu)
        if isValidShrubPDU(pdu_):
            (typeseq, msg) = interpretShrubPDU(pdu_)
            shrub.append((ts, typeseq, msg))
            pdu = bytearray()
    return (pdu, shrub)

def parseShrubFromFile(fname, src):
    shrub = []
    buff = bytearray()
    try:
        with open(fname, "rb") as fh:
            while True:
                (psrc, ts, data) = readLinMonEntry(fh)
                if psrc == src:
                    buff.extend(data)
                    (buff, shrub) = parseShrubFromBuffer(buff, shrub, ts)
                    
    except Exception as e:
        pass
    return shrub

def timeDiffToSecs(tdiff):
    # N.B. assumes tdiff.days = 0
    return '{}.{:06d}'.format(tdiff.seconds, tdiff.microseconds)

def writeCSV(fname, data, tmin):
    with open(fname, "w") as fh:
        fh.write('"Number","Time(s)","Type/SEQ","Type"\n')
        n = 1
        for (ts, typeseq, msg) in data:
            fh.write('{},{},{},"{}"\n'.format(n, timeDiffToSecs(ts - tmin), typeseq, msg))
            n += 1

def analyseFile(fname):
    adata = parseShrubFromFile(fname, 'COM2:') # Traffic from the BLU (Rx)
    bdata = parseShrubFromFile(fname, 'COM1:') # Traffic from the Gate (Tx)
    tmin = min(adata[0][0], bdata[0][0])
    writeCSV(csvA, adata, tmin)
    writeCSV(csvB, bdata, tmin)
    sa02.analyseFile('CSV')
    os.remove(csvA)
    os.remove(csvB)

if len(sys.argv) < 2:
    raise Exception('No files specified!')

for fname in sys.argv[1:]:
    analyseFile(fname)
