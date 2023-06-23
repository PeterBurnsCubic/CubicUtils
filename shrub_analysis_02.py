#!/usr/bin/env python3

import sys
import pandas
from collections import defaultdict

def analyseFile(fstem):
    print(fstem)
    print('------------------------')

    # parse CSV files, combine and sort by ascending "Time(s)"
    dfA = parseCSVFile(fstem, 'A', 'BLU')   # 'A' traffic is from the BLU
    dfB = parseCSVFile(fstem, 'B', 'Gate')  # 'B' traffic is from the Gate
    df = pandas.concat([dfA, dfB]).sort_values(by='Time(s)')

    # reports
    reportACKStats(df, 'Gate', 'BLU')
    reportACKStats(df, 'BLU', 'Gate')
    print('')

def parseCSVFile(fstem, aorb, src):
    fname = '{}_{}.csv'.format(fstem, aorb)
    types = defaultdict(lambda : str)
    types['Number'] = int
    types['Time(s)'] = float
    types['Length(s)'] = float
    types['Distance(s)'] = float
    df = pandas.read_csv(fname, index_col='Number', dtype=types, keep_default_na=False)
    df['Source'] = [src] * df.shape[0]
    return df

def reportACKStats(df, src, dst):
    waitForAck      = False
    lastTypeSeq     = ''
    lastMsgTimetamp = 0.0
    nValidAcks      = 0
    nSpuriousAcks   = 0
    maxAckTime      = 0.0
    minAckTime      = 1.0
    totalAckTime    = 0.0
    nUniqueMsg      = 0
    nRetransmit     = 0
    for index, row in df.iterrows():
        msgtype   = row['Type']
        if len(msgtype) > 0:
            timestamp = row['Time(s)']
            if row['Source'] == src:
                typeSeq   = row['Type/SEQ']
                if msgtype[0:3] != 'ACK':
                    # message from the source (not an ACK)
                    if typeSeq == lastTypeSeq:
                        nRetransmit += 1
                    else:
                        nUniqueMsg  += 1
                    lastTypeSeq      = typeSeq
                    lastMsgTimestamp = timestamp
                    waitForAck       = True
            elif msgtype[0:3] == 'ACK':
                # ACK from the destination
                if waitForAck:
                    nValidAcks   += 1
                    ackTime      = timestamp - lastMsgTimestamp
                    totalAckTime += ackTime
                    if ackTime > maxAckTime:
                        maxAckTime = ackTime
                    if ackTime < minAckTime:
                        minAckTime = ackTime
                    waitForAck = False
                else:
                    nSpuriousAcks += 1

    # print the report
    print('')
    print('Messages from {}, ACKs from {}'.format(src, dst))
    print('')
    print('Average ACK time:          {:.3f}'.format(totalAckTime/nValidAcks))
    print('Shortest ACK time:         {:.3f}'.format(minAckTime))
    print('Longest ACK time:          {:.3f}'.format(maxAckTime))
    print('Number of Retransmissions: {}/{} ({:.1f}%)'.format(nRetransmit, nUniqueMsg, (nRetransmit/nUniqueMsg)*100))
    print('Number of Spurious ACKs:   {}'.format(nSpuriousAcks))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('')
        print('Usage: {} filestem [filestem...]'.format(sys.argv[0]))
        print('where filestem is the start of a csv filename with _A and _B variants')
        print('e.g. use filestem = "power_01" for power_01_A.csv and power_01_B.csv')
        print('')
    else:
        for fstem in sys.argv[1:]:
            analyseFile(fstem)
