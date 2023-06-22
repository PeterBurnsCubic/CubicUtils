#!/usr/bin/env python3

import sys
import pandas
from collections import defaultdict

def analyseFile(fname):
    print(fname)
    print('------------------------')

    # parse CSV file
    types = defaultdict(lambda : str)
    types['Number'] = int
    types['Time(s)'] = float
    types['Length(s)'] = float
    types['Distance(s)'] = float
    df = pandas.read_csv(fname, index_col='Number', dtype=types, keep_default_na=False)

    # reports
    reportNumberOfPacketsByType(df)
    # reportStaticStatusQueries(df)
    reportPacketRetransmissions(df)
    reportRepeatedACKs(df)
    reportPacketFailures(df)

def reportNumberOfPacketsByType(df):
    # count the packets
    typeDict = {}
    numAckIn = 0
    numRpyIn = 0
    numAckOut = 0
    numCmdOut = 0
    numOther = 0
    for index, row in df.iterrows():
        name = row['Type']
        if name in typeDict:
            typeDict[name] += 1
        else:
            typeDict[name] = 1
        if name == 'ACK =>':
            numAckOut += 1
        elif name == 'ACK <=':
            numAckIn += 1
        elif name[0:2] == '=>':
            numCmdOut += 1
        elif name[0:2] == '<=':
            numRpyIn += 1
        else:
            numOther += 1

    # print the report
    total = 0
    fmt = '{:30}{}'
    print('')
    print(fmt.format('Packet Type', 'Number Logged'))
    for item in typeDict.items():
        print(fmt.format(item[0], item[1]))
        total += item[1]
    print(fmt.format('Total', total))
    total = 0
    print('')
    print(fmt.format('Packet Type', 'Number Logged'))
    print(fmt.format('Requests =>', numCmdOut))
    print(fmt.format('ACKs <=', numAckIn))
    print(fmt.format('Replies <=', numRpyIn))
    print(fmt.format('ACKs =>', numAckOut))
    if numOther > 0:
        print(fmt.format('Other', numOther))
    print('')

def reportPacketRetransmissions(df):
    print('')
    lastTypeSeqIn = ''
    lastTypeSeqOut = ''
    for index, row in df.iterrows():
        cmd = row['Type']
        if 'ACK' not in cmd:
            typeseq = row['Type/SEQ']
            if '<=' in cmd:
                if typeseq == lastTypeSeqIn:
                    print('Repeat "{}" (Type/SEQ {}) at {})'.format(cmd, typeseq, row['Date/Time']))
                lastTypeSeqIn = typeseq
            elif '=>' in cmd:
                if typeseq == lastTypeSeqOut:
                    print('Repeat "{}" (Type/SEQ {}) at {})'.format(cmd, typeseq, row['Date/Time']))
                lastTypeSeqOut = typeseq
    print('')

def reportAckList(ackList):
    if len(ackList) > 1:
        print('{} ACK <= at {}'.format(len(ackList), ackList))

def reportRepeatedACKs(df):
    print('')
    ackInList = []
    ackOutList = []
    for index, row in df.iterrows():
        cmd = row['Type']
        if '<=' in cmd:
            if 'ACK' not in cmd:
                reportAckList(ackInList)
                ackInList = []
                ackOutList = []
            else:
                ackInList.append(row['Date/Time'])
        else:
            if 'ACK' not in cmd:
                reportAckList(ackOutList)
                ackOutList = []
                ackInList = []
            else:
                ackOutList.append(row['Date/Time'])
    reportAckList(ackInList)
    reportAckList(ackOutList)
    print('')

def reportPacketFailures(df):
    print('')
    foundNak = False
    for index, row in df.iterrows():
        if 'NAK' in row['Type']:
            print('{} at {}, '.format(row['Type'], index, row['Date/Time']))
            foundNak = True
    if not foundNak:
        print('No NAKs found')
    print('')

def reportStaticStatusQueries(df):
    print('')
    numQueries = 0
    startTime = 0.0
    endTime = 0.0
    for index, row in df.iterrows():
        cmd = row['Type']
        time = row['Time(s)']
        if cmd == '=> Static status query':
            if numQueries == 0:
                startTime = time
            numQueries += 1
            endTime = time
    print('Number of Static Status Queries = {} in {}s'.format(numQueries, endTime-startTime))
    print('')

if len(sys.argv) < 2:
    raise Exception('No files specified!')

for fname in sys.argv[1:]:
    analyseFile(fname)
