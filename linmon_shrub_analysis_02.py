#!/bin/python3

import sys
import os
import struct
import xlrd
import shrub_analysis_02 as sa02
import datetime

csvA = "CSV_A.csv"
csvB = "CSV_B.csv"

def findFirstLinMonEntry(fh):
    data = fh.read(100)
    pos = data.find(b'COM')
    if pos < 0:
        raise Exception('Could not find COM in first 100 bytes')
    fh.seek(pos)

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

def parseShrubFromBuffer(buff, shrub, n, ts):
    pdu = bytearray()
    found = False
    for b in buff:
        if b == 1:
            if len(pdu) > 0:
                print('Ignoring invalid data (not SHrUB): {}'.format(pdu))
            pdu = bytearray()
        pdu.append(b)
        pdu_ = removeShrubTransparency(pdu)
        if isValidShrubPDU(pdu_):
            found = True
            (typeseq, msg) = interpretShrubPDU(pdu_)
            shrub.append((n, ts, typeseq, msg))
            pdu = bytearray()
    return (found, pdu, shrub)

def parseShrubFromFile(fname):
    shrub1 = []
    shrub2 = []
    buff1 = bytearray()
    buff2 = bytearray()
    n = 1
    try:
        with open(fname, "rb") as fh:
            findFirstLinMonEntry(fh)
            while True:
                (psrc, ts, data) = readLinMonEntry(fh)
                if psrc == 'COM1:':
                    buff1.extend(data)
                    found = True
                    while found:
                        (found, buff1, shrub1) = parseShrubFromBuffer(buff1, shrub1, n, ts)
                        n += 1
                elif psrc == 'COM2:':
                    buff2.extend(data)
                    found = True
                    while found:
                        (found, buff2, shrub2) = parseShrubFromBuffer(buff2, shrub2, n, ts)
                        n += 1
                else:
                    print('Ignoring spurious data id "{}"'.format(psrc))    
                    
    except Exception as e:
        pass
    return (shrub1, shrub2)

def timeDiffToSecs(tdiff):
    # N.B. assumes tdiff.days = 0
    return '{}.{:06d}'.format(tdiff.seconds, tdiff.microseconds)

def writeCSV(fname, data, tmin, tstart, tend):
    with open(fname, "w") as fh:
        fh.write('"Number","Time(s)","Type/SEQ","Type"\n')
        for (n, ts, typeseq, msg) in data:
            if ts >= tstart and ts <= tend:
                fh.write('{},{},{},"{}"\n'.format(n, timeDiffToSecs(ts - tmin), typeseq, msg))

def analyseFile(fname, start_datetime, end_datetime):
    (bdata, adata) = parseShrubFromFile(fname) # 'COM1' is Tx (gate to BLU), which is 'B' traffic for our script
    tmin = min(adata[0][1], bdata[0][1])
    writeCSV(csvA, adata, tmin, start_datetime, end_datetime)
    writeCSV(csvB, bdata, tmin, start_datetime, end_datetime)
    sa02.analyseFile('CSV')
    os.remove(csvA)
    os.remove(csvB)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('')
        print('Usage: {} linmon_binary_filename [start_datetime end_datetime]'.format(sys.argv[0]))
        print('start and end datetimes are optional, else must be specified as "yyyy-mm-dd HH:MM:SS"')
        print('')
    else:
        fname = sys.argv[1]
        start_datetime = datetime.datetime.strptime(sys.argv[2] if len(sys.argv) > 2 else '1900-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        end_datetime   = datetime.datetime.strptime(sys.argv[3] if len(sys.argv) > 3 else '2100-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        analyseFile(fname, start_datetime, end_datetime)
