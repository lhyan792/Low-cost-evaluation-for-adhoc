from os import makedirs
from os.path import join, isdir
import sys,getopt
from random import sample
from writeqrel import *


repeattime=30
topk=20
#parsing arguments
opts, args = getopt.getopt(sys.argv[1:],"q:p:r:j:o:")
for opt, arg in opts:
    if opt=='-q':
        qid=int(arg)
    if opt=='-p':
        samplerate=float(arg)
    if opt=='-o':
        outputfolder=str(arg)
    if opt=='-r':
        trecrunf=str(arg)
    if opt=='-j':
        qrelf=str(arg)

def readtrecrun(runf):
    trf=open(runf,'r')
    runcwids=set()
    for line in trf:
        linearray=line.split()
        pos=int(linearray[3])
        if pos > topk:
            continue
        cwid=str(linearray[2])
        runcwids.add(cwid)
    trf.close()
    return runcwids


# {cwid:jud}
def readqrel(qrelf):
    qrelF=open(qrelf,'r')
    relcwidjud=dict()
    irlcwidjud=dict()
    cwidjud=dict()
    for line in qrelF:
        linearray=line.split()
        cwid=linearray[2]
        if cwid not in runcwids:
            continue
        jud=int(linearray[3])
        cwidjud[cwid]=jud
        if jud > 0:
            relcwidjud[cwid]=jud
        else:
            irlcwidjud[cwid]=jud
    qrelF.close()
    return cwidjud, relcwidjud, irlcwidjud
runcwids = readtrecrun(trecrunf)
cwidjud, relcwidjud, irlcwidjud = readqrel(qrelf)
relcwids = relcwidjud.keys()
irlcwids = irlcwidjud.keys()
relnum = len(relcwids)
irlnum = len(irlcwids)
docs=list(runcwids)

def sampling():
    if relnum > 0:
        sampledrel=int(samplerate*relnum) if (samplerate*relnum > 1) else 1
        sampledrels= sample(relcwids,sampledrel)
    else:
        print qid,'does not have relevant judgment'
    if irlnum > 0:
        sampledirl=int(samplerate*irlnum) if (samplerate*irlnum > 10) else 10
        sampledirrels= sample(irlcwids,sampledirl)
    else:
        print qid,'does not have irrelevant judgment'
    cwids=list(set(sampledrels)|set(sampledirrels))
    return cwids

count=repeattime
while count > 0:
    outdir = join(outputfolder, str(samplerate), str(count))
    if not isdir(outdir):
        makedirs(outdir)
    outbqrel=open(join(outdir, str(qid) + ".bqrel"),'w')
    outoqrel=open(join(outdir, str(qid) + ".oqrel"),'w')
    L = sampling()
    outbqrel.write(bqrel(qid, L,cwidjud,docs))
    outoqrel.write(oqrel(qid, L,cwidjud,docs))
    outbqrel.close()
    outoqrel.close()
    count -= 1
