import getopt,sys
from os.path import isdir, join
from os import makedirs
import numpy as np
from writeqrel import *
from collections import Counter
from numpy.random import choice
import math

topk=20
ispool=False
opts, args = getopt.getopt(sys.argv[1:],"j:o:q:r:p:i:a:")
for opt, arg in opts:
    if opt=='-o':
        outdir=str(arg)
    if opt=='-i':
        outipdir=str(arg)
    if opt=='-q':
        qid=int(arg)
    if opt=='-r':
        trecrunf=str(arg)
    if opt=='-j':
        qrelf=str(arg)
    if opt=='-p':
        percent=float(arg)
    if opt=='-a':
        # percent of additional judgments from depth pooling
        poolp=float(arg)
        if poolp > 0:
            ispool=True

if not isdir(outdir):
    makedirs(outdir)
if not isdir(outipdir):
    makedirs(outipdir)


def readtrecrun(runf):
    trf=open(runf,'r')
    runcwids=set()
    cwidsysrank=dict()
    for line in trf:
        linearray=line.split()
        pos=int(linearray[3])
        if pos > topk:
            continue
        cwid=str(linearray[2])
        runname=str(linearray[5])
        runcwids.add(cwid)
        if cwid not in cwidsysrank:
            cwidsysrank[cwid]=dict()
        cwidsysrank[cwid][runname]=pos
    trf.close()
    return runcwids, cwidsysrank

# {cwid:jud}
def readqrel(qrelf):
    qrelF=open(qrelf,'r')
    cwidjud=dict()
    for line in qrelF:
        linearray=line.split()
        cwid=linearray[2]
        jud=int(linearray[3])
        cwidjud[cwid]=jud
    qrelF.close()
    return cwidjud

def apprior(cwidsys):
    docweight = dict()
    weightdocs = dict()
    const = 1.0 / (2 * topk)
    for cwid in cwidsys:
        weight = sum([(const * math.log(topk / float(rank), 2)) for rank in cwidsys[cwid].values()])
        weight /= len(cwidsys[cwid])
        docweight[cwid] = weight
        if weight not in weightdocs:
            weightdocs[weight]=list()
        weightdocs[weight].append(cwid)
    return docweight, weightdocs


def incrementalpool(trecf):
    trf=open(trecf,'r')
    poscwids = dict()
    cwidpos = dict()
    for line in trf:
        linearray=line.split()
        pos=int(linearray[3])
        if pos > topk:
            continue
        qid=int(linearray[0])
        cwid=str(linearray[2])
        run=str(linearray[5])
        if cwid not in cwidpos:
            cwidpos[cwid]=list()
        cwidpos[cwid].append(pos)
    cwids=cwidpos.keys()
    trf.close()
    for cwid in cwidpos:
        mpos = min(cwidpos[cwid])
        avepos = sum(cwidpos[cwid]) / float(len(cwidpos[cwid]))
        if mpos not in poscwids:
            poscwids[mpos] = dict()
        if avepos not in poscwids[mpos]:
            poscwids[mpos][avepos]=list()
        poscwids[mpos][avepos].append(cwid)
    posaccnum = dict()
    accnum = 0
    for pos in sorted(poscwids.keys()):
        for v in poscwids[pos]:
            accnum += len(poscwids[pos][v])
        posaccnum[pos] = accnum
    return poscwids, posaccnum

######################################################
# read in the data
######################################################
# read in selected qrel qid-[cwids]
cwidjud = readqrel(qrelf)
# read in trecruns
runcwids, docsysrank = readtrecrun(trecrunf)
# intereaction of different sources' cwid
icwids=set.intersection(set(cwidjud.keys()), runcwids)

docs=list(runcwids)
cwids=list()
cwidsysrank=dict()
for cwid in icwids:
    cwids.append(cwid)
    cwidsysrank[cwid]=dict(docsysrank[cwid])
docweight, weightdocs = apprior(cwidsysrank)
mtotal = int(round(len(runcwids) * percent))
if ispool:
    m = int(round(mtotal * (1 - poolp)))
    mpool = mtotal - m
    poscwids, posaccnum = incrementalpool(trecrunf)
else:
    m = mtotal


cwidinProb=dict()
if ispool:
    finished=False
    for pos in sorted(poscwids.keys()):
        for avepos in sorted(poscwids[pos].keys()):
            for cwid in poscwids[pos][avepos]:
                if len(cwidinProb) >= mpool:
                    finished=True
                    break
                cwidinProb[cwid] = 1
            if finished:
                break
        if finished:
            break


stratify=list()
binws = list()
unibin=list()
binweight=0
for w in sorted(weightdocs.keys(), reverse=True):
    for cwid in weightdocs[w]:
        if len(unibin) >= m:
            stratify.append(list(unibin))
            binws.append(binweight)
            unibin = list()
            binweight = 0
        unibin.append(cwid)
        binweight += w
if len(unibin) > 0:
    stratify.append(list(unibin))
    binws.append(binweight)

if len(binws) == 0:
    print qid, outdir, "binidx is empty"
    sys.exit()


binidx = range(len(binws))
binprob = [binws[i] / sum(binws)  for i in range(len(binws))]

sampledidx = choice(binidx, m, replace=True, p=binprob)
bidxCount=Counter(sampledidx)
L = list()
inProb = list()
for bidx in sorted(bidxCount.keys()):
    docnum = bidxCount[bidx]
    prob = binprob[bidx]
    selectedDoc = choice(stratify[bidx], docnum, replace=False)
    for cwid in selectedDoc:
        if cwid not in cwidinProb:
            cwidinProb[cwid]=prob

outbqrel=open(join(outdir, str(qid) + ".bqrel"),'w')
outoqrel=open(join(outdir, str(qid) + ".oqrel"),'w')
outprel=open(join(outipdir, str(qid) + ".prel"),'w')
outbqrel.write(bqrel(qid,L,cwidjud,docs))
outoqrel.write(oqrel(qid,L,cwidjud,docs))
outprel.write(prel(qid,cwidjud,docs, cwidinProb))
outbqrel.close()
outoqrel.close()
outprel.close()
