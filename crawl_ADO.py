''' crawl_ADV: utilities to crawl ADVina FAAH files
    was part of get_ADInfo

@version 1.0
@date on 30 Aug 14
@author: rbelew@ucsd.edu, dsantiago@scripps.edu
'''

import sys
# import getopt
import re
import glob
import os
import csv

import tempfile
import tarfile
import shutil
import json
import argparse
import datetime

# from AutoDockTools.HelperFunctionsN3P import pathToList, getLines, percent
from string import strip
def getLines(filename, doStrip = False, removeEmpty=False):
    """ """
    f = open(filename, 'r')
    lines = f.readlines()
    f.close()
    if doStrip:
        lines = map(strip,lines)
    if removeEmpty:
        #lines = removeEmptyLines(lines)
        lines = [ l for l in lines if l.strip() ]
    return lines

# defaults
mode = "1" # ONLY pose for Vina
ebest = -999. # energy
eworst = -3.
cworst = 1. # cluster poses
cbest = 999.
pworst = 1. # cluster %
pbest = 100.
lworst = 0. # ligand efficiency
lbest = -99
DEBUG = False
pattern = "_VS.pdbqt" # default pattern for searching result files
#pattern = ".VS.pdbqt" # default pattern for searching result files
do_filter = False
recursive = False

## Shared with AutoDock

AADict = {'ASP':'D', 'GLU':'E', 'LYS':'K', 'HIS':'H', 'ARG':'R',
               'GLN':'Q', 'ASN':'N', 'SER':'S', 'ASX':'B', 'GLX':'Z',
               'PHE':'F', 'TRP':'W', 'TYR':'Y',
               'GLY':'G', 'ALA':'A', 'ILE':'I', 'LEU':'L', 'CYS':'C',
               'MET':'M', 'THR':'T', 'VAL':'V', 'PRO':'P',
               'HID':'H', 'HIE':'H', 'HIP':'H',
               'ASH':'D', 'GLH':'E',
               'LYN':'K', 'ARN':'R',
               'HOH':'U', 'CL': 'J' }

ADbatchRE = r'FAHV_(x?)(.+)_([0-9]+)_processed.tgz'
ADbatchREPat = re.compile(ADbatchRE)

InterTypes = ('hba', 'hbd', 'mtl','ppi','tpi','vdw')
InterRE = r'(.*):.+():([A-Z]+[0-9]*)~~(.*):(.+):(.+)'

InterREPat = re.compile(InterRE)
# vdw are different
# :CYS65:SG
# InterVDWRE = r'(.*):([A-Z]+[0-9]+):([A-Z]+)'
InterVDWRE = r'(.*):(.+):(.+)'
InterVDWREPat = re.compile(InterVDWRE)
# ppi/tpi are different
# B:HIS114~~(-4.295,-13.390,-20.427:-3.408,-10.290,-18.368)
# cf. piStackingAndRingDetection.findLigRecPiStack()
# pstack.append([res, rec_centroid, lig_centroid])
InterPiRE = r'(.*):(.+)~~\(([-.,0-9]+):([-.,0-9]+)\)'
InterPiREPat = re.compile(InterPiRE)

def reducePlusInterDict(ligData):
    '''create sparse version of interaction dict, with only ligands atom type (not its index)
       the syntax for the InterPattern seems a PDB convention?
    '''
    
    rinterDict = {}
    for itype in InterTypes:
        if len(ligData[itype]) > 0:
            rinterDict[itype] = []
            if itype=='vdw':
                for inter in ligData[itype]:
                    # d:<0>:O3~~B:ARG57:N
                    # :LEU63:CD1 -->actual example, matches InterVDWREPat \dns
                    m = InterVDWREPat.match(inter)
                    try:
                        (rchain,raa,ratom) = m.groups()
                        rinterDict[itype].append( (rchain,raa,ratom) )
                    except:
                        print 'reducePlusInterDict: bad vdw string?!',inter
            elif itype=='ppi' or itype=='tpi':
                for inter in ligData[itype]:
                    # d:<0>:O3~~B:ARG57:N
                    m = InterPiREPat.match(inter)
                    try:
                        (rchain,raa,rcenter,ligcenter) = m.groups()
                        rinterDict[itype].append( (rchain,raa,rcenter,ligcenter) )
                    except:
                        print 'reducePlusInterDict: bad ppi/tpi string?!',inter
            else:
                for inter in ligData[itype]:
                    # d:<0>:O3~~B:ARG57:N
                    m = InterREPat.match(inter)
                    try:
                        # (ligIdx,liname,rchain,raa,ratom) = m.groups()
                        (lchain,lres,latom,rchain,raa,ratom) = m.groups()
                        rinterDict[itype].append( (rchain,raa,ratom,latom) )
                    except:
                        print 'reducePlusInterDict: bad %s string?! %s' % (itype,inter)
            
    return rinterDict

#############################################################################
# from rabbit
# Author: Stefano FORLI
#
# Copyright: Stefano Forli, TSRI 2011
#
# v.0.4
#############################################################################

def checkVSresult_ADV(lines):
    "parses and validates a PDBQT+ file (lines)"
    if lines[0].startswith("USER    ADVS_Vina_result>"):
        return True
    else:
        return False

def setKwMode_ADV(mode = "1"):
    # USER ADVina_pose1> -10.200, -0.309
    # mode = "1", "2", "..."
    if mode == "any":
        kw = "ADVina_pose."
    else:
        kw = "ADVina_pose"+mode
    return kw

def getResultCount_ADV(lines):
    return int(lines[4].split("ADVina_results>")[1].strip())
    
def getRawEnergyData_ADV(lines, mode = "1"):
    # mode = "1", "2", "...", "any" (POSES)
    # format: { "e" : [ float(e)] , "leff" : [float(leff)] }
    kw = setKwMode_ADV(mode)+">"
    result = { "e" : [],
                "leff" : [] }
    for l in lines:
        if re.search(kw, l):
            l = l.split(">", 1)[1]
            e, leff = l.split(",")
            result['e'].append(float(e))
            result["leff"].append(float(leff))
            if not mode == "any":
                break
    return result

def getLigInteractions_ADV(lines, mode = "1"):
    kw = setKwMode_ADV(mode) #
    kw += "_" # TODO test this!
    interactions = {"vdw" : [], # these keys must match the
                    "hba" : [], # tags used in writing the PDBQT+
                    "hbd" : [],
                    "ppi" : [],
                    "tpi" : [],
                    "mtl" : [],
                    }
    for l in lines:
        if re.search(kw, l):
            for itype in interactions.keys():
                if (itype == "ppi") or (itype == "tpi"):
                    sep = ";"
                else:
                    sep = ","
                if itype in l:
                    l = l.split(itype+">", 1)[1]
                    l = l.split(sep)
                    for i in l:
                        interactions[itype].append(i.strip())
    return interactions

def getLigSource_ADV(lines):
    srcPrefix = 'USER    ADVina_pose'
    src = ''
    for l in lines:
        if l.startswith(srcPrefix):
            src = l[len(srcPrefix):].strip()
            return src
    return src

def getGenericData_ADV(lines):
    receptNamePrefix = 'USER    ADVina_rec> '
    nresultPrefix = 'USER    ADVina_results> '
    rname = ''
    nresult = 0
    for l in lines:
        if l.startswith(receptNamePrefix):
            rname = l[len(receptNamePrefix):].strip()
        if l.find(nresultPrefix) != -1:
            nresult = int(l[len(nresultPrefix):].strip())

    return (rname,nresult)
    
def parseADPDBQT_ADV(f):
    ligand = getLines(f)
    if not checkVSresult_ADV(ligand):
        return None

    ligData = {}
    rname,nresult = getGenericData_ADV(ligand)
    
    if rname=='':
        print 'parseADPDBQT_ADV: missing receptor name?!',f
        ligData['recept'] = ''
    else:
        ligData['recept'] = rname
    
    if nresult==0:
        print 'parseADPDBQT_ADV: missing results?!',f
        ligData['nresult'] = 0
        return None
    else:
        ligData['nresult'] = nresult
        
    ## ADVina has one
    src = getLigSource_ADV(ligand)
    if src=='':
        print 'parseADPDBQT_ADV: missing src?!',f
        ligData['nresult'] = 0
    else:
        ligData['src'] = src
    
    ligdataRaw = getRawEnergyData_ADV(ligand)
    # dict: {'c_pc': [53.45], 'e': [-6.19], 'leff': [-0.413], 'c_size': [93]}

    for k,v in ligdataRaw.items():
        ligData[k] = v[0]
        
    liginteract = getLigInteractions_ADV(ligand)
    reducedInterDict = reducePlusInterDict(liginteract)
    ligData.update(reducedInterDict)
                   
    return ligData
        

# simplified, here, means that this should work for all batches after ??? Exp.# ???
# because naming was simplified (by dns)
# ADVsimple = r'fahv.x([a-zA-Z0-9]+)(_[A-Z0-9]*)*_(ZINC[0-9]+)(_[0-9]*)*_([0-9]+)_out_Vina_VS.pdbqt'
#ADVsimple = r'fahv.x([a-zA-Z0-9]+)_(.+)_([0-9]+)_out_Vina_VS.pdbqt'
# OET1 pattern different from FAHV (switch rec and batch)
ADVsimple = r'fahv.([0-9]+)_x([a-zA-Z0-9]+)_(.+)_out_Vina_VS.pdbqt'
ADVsimplePat = re.compile(ADVsimple, re.IGNORECASE)

def visit_ADV_tgz(tgzPath,exptname,recon,verbose,receptor):

    dataTbl = {}
    # 2do: Py2.7 allows WITH context management! TODO
# with tarfile.open(tgzPath) as subTar:
# with tarfile.open(subTar) as dataDir:
    #tmpDir = tempfile.mkdtemp()
    tmpDir = 'scratchV'
    os.mkdir(tmpDir)
    try:
        allTar = tarfile.open(tgzPath)
    except Exception,e:
        print 'visit_ADV_tgz: cant open',e,tgzPath
        return None
        
    allTar.extractall(tmpDir)

    # ASSUME: _VS "bar" style processed file names for ADV
    # fahv.x4I7G_RT_NNRTIadj_wNNRTI_ZINC58421065_1_649284996_out_Vina_VS.pdbqt
    # Exp79/Results_x3kf0A/FAHV_x3kf0A_0124403_processed.tgz example:
    #  FAHV_x3kf0A_0124403_processed/ # (untarred dir)
    #    fahv.x3kf0A_ZINC01569654_1113915765_out_Vina_VS.pdbqt

    procList = glob.glob(tmpDir+'/FAHV*/fahv.*_out_Vina_VS.pdbqt')
    if verbose:
        print 'visit_ADV_tgz: NTGZ=',len(procList)
        
    for isd,procPath in enumerate(procList):
        # fahv.x3kf0A_ZINC00145439_2057149382_out_Vina_VS.pdbqt
        procBits = os.path.split(procPath)

        # NB: don't need to capture batchNo; visitRpt_ADV_tgz() has it!
        # /tmp/tmpmmBQ7D/FAHV_x3kf0A_0124412_processed
        # dirBits = procBits[0].split('_')
        # batchNo = int(dirBits[2])

        procf = procBits[1]

        # dns - use receptor to get ligand
        # example: fahv.x4GW6aINleA_ZINC29590323_491341659_out_Vina_VS.pdbqt
        #proLigandWorkUnit=procf.lstrip('fahv.'+receptor+'_')
        totalPrefixLen=len('fahv.')+len(receptor)+len('_')
        proLigandWorkUnit=procf[totalPrefixLen:]

        # and then: ZINC29590323_491341659_out_Vina_VS.pdbqt
        #ligandWorkUnit=proLigandWorkUnit.rstrip('_out_Vina_VS.pdbqt')
        ligandWorkUnit=proLigandWorkUnit[:-1*len('_out_Vina_VS.pdbqt')]

        getWorkUnit=ligandWorkUnit.rindex('_')
        ligand=ligandWorkUnit[:getWorkUnit] # dns ligand defined
        workNo=ligandWorkUnit[(getWorkUnit+1):] # dns workNo defined
        # dns - use receptor to get ligand

        # lbpos = procf.find('_')
        # rbpos = procf.rfind('_')
        # assert (lbpos != -1 and rbpos != -1 and rbpos > lbpos), 'visit_ADV_tgz: bad procf?! %s' % (procf)
        # ligand = procf[lbpos+1:rbpos]
        
        # dns - commented code for regex (below); using naming convention to get ligand, receptor
              # Results_<receptor> --> receptor
              # fahv.<receptor>_<ligand>_<workNo>_out_vina_VS.pdbqt

        #mpath = ADVsimplePat.match(procf)
        #try:
        #    (receptor,ligand,workNo) = mpath.groups()
        #except Exception,e:
        #    print 'visit_ADV_tgz: broken ADVsimplePat.match',e,procf
        # import pdb; pdb.set_trace()
        
        ###-------
        ligData = parseADPDBQT_ADV(procPath)
        ###-------
        
        if not(ligData):
            print 'visit_ADV_tgz: invalid ADV file?!',procf, tgzPath
            continue

        dk = (exptname,receptor,ligand)
        
        if dk in dataTbl:
            print 'visit_ADV_tgz: dup dataKey?!',dk
            continue

        dataTbl[dk] = ligData
# Need to remove files in scrath directory

#for fl in glob.glob("E:\\test\\*.txt"):
#    #Do what you want with the file
#    os.remove(fl)
        #for oldfile in glob.glob(tmpDir+"/*"):
            #os.removedirs(oldfile)
            #shutil.rmtree(oldfile)
                                 
    shutil.rmtree(tmpDir)
    # print 'visit_ADV_tgz: done.',len(dataTbl)
    
    return dataTbl

def rptData_ADV(dataTbl,summf,interf,exptname,batchNo):
    '''V1: produce condensed JSON inter file
            [ [Expt,BatchNo,Recept,Lig, [IType,[InterEnum] ] ] ]
            ala ["Exp96", 197339, "x3ZSW_B_IN_Y3", "Y3_ZINC00626007", [[0, [["B", "R199", "NH2", "O1"], ["B", "K188", "NZ", "O2"]]], [5, [["B", "G82", "CA"], ..., ["B", "I141", "O"]]]]]
    '''
    
    summs = open(summf,'w')
    summs.write('Expt,Batch,Recept,Ligand,E,Eff,Nvdw,Ninter\n')
    
    allInter = []
    for dk in dataTbl:
        (exptname,receptor,lig) = dk
        ligData = dataTbl[dk]
        ninter = 0
        nvdw = 0
        for itype in InterTypes:
            if itype in ligData:
                if itype=='vdw':
                    nvdw = len(ligData['vdw'])
                else:
                    ninter += len(ligData[itype])

        summs.write('%s,%d,%s,%s,%s,%s,%d,%d\n' % \
                   (exptname,batchNo,ligData['recept'],lig,\
                    ligData['e'],ligData['leff'],nvdw,ninter))
                

        interInfo = [exptname, batchNo, ligData['recept'], lig]
        interList = []
        
        for itype in InterTypes:
            if itype in ligData:
                # additional compression by combining all inter of same type
                itlist = []
                # convert itype string to its index in InterTypes
                itypeIdx = InterTypes.index(itype)

                for interTuple in ligData[itype]:
                    inter = list(interTuple)
                    
                    # convert 3-letter receptor AA to single char
                    raa = inter[1]
                    raalet3 = raa[:3]
                    raalet2 = raa[:2] # check for CL and adjust following code
                    pos = raa[3:]       # for correct res number
                    pos2 = raa[2:]
                    pos21 = raa[2:3]
                    if raalet3 in AADict:
                        raaLet = AADict[raalet3]
                        inter[1] = raaLet+pos
                    elif raalet2 in AADict:
                        raaLet = AADict[raalet2]
                        inter[1] = raaLet+pos2
                    else:
                        raaLet = 'X'
                        if re.match("[0-9]", pos21):
                            inter[1] = raaLet+pos2
			else:
                            inter[1] = raaLet+pos
                    
                    itlist.append(inter)
                    
                interList.append( [itypeIdx,itlist] )
                    
        interInfo.append(interList)
        
        allInter.append(interInfo)
        
    summs.close()
                  
    inters = open(interf,'w')
    json.dump(allInter,inters)
    inters.close()


def visitRpt_ADV_tgz(tgzPath,recon,batchTbl,outdir,tocs,exptname,batchNo,verbose,receptor):
    ''' get info, place in this table
    	info is extracted from enhanced pdbqt files inside tarball
    '''	

    dataTbl = visit_ADV_tgz(tgzPath,exptname,recon,verbose,receptor)
    if not dataTbl:
        print 'visitRpt_ADV_tgz: no dataTbl?!',tgzPath,exptname
        return 0
        
    if recon:
        print 'visitRpt_ADV_tgz: Recon-only; no reporting'
        return len(dataTbl)
        
    summf  = outdir+'/'+exptname+'/summ/ADV_summ_%07d.csv' % (batchNo)
    interf = outdir+'/'+exptname+'/inter/ADV_inter_%07d.json' % (batchNo)
    rptData_ADV(dataTbl,summf,interf,exptname,batchNo)
    
    #tocStr = '%s,%05d,%d,%s' % (exptname,ntgz,len(dataTbl),tgzPath)
    tocStr = '%s,%d,%d,%s' % (exptname,batchNo,len(dataTbl),tgzPath)
    if verbose:
        print 'visitRpt_ADV_tgz toc:',tocStr
            
    tocs.write(tocStr+'\n')
    # fun2watch! toc
    tocs.flush(); os.fsync(tocs.fileno())
    
    return len(dataTbl)

def mglTop_visit_ADV(ADV_topDir,outdir,exptList=None,recon=False,verbose=False):
    'recon stops after opening, parsing one file in first tgz'
    
    if exptList:
        print 'mglTop_visit_ADV: Explicit experiment list %s' % (str(exptList))
    else:
        crawlPat = ADV_topDir+'/Exp*'
        print 'mglTop_visit_ADV: Full crawl of %s' % (crawlPat)
        exptList = [os.path.split(exptPath)[1] for exptPath in glob.glob(crawlPat) ]
        
    print 'mglTop_visit_ADV: NExperiments=',len(exptList)
    
    if verbose:
        print 'mglTop_visit_ADV: **Verbose output'

    if recon:
        print 'mglTop_visit_ADV: **Reconnaissance sniffing only!'

    totParse = 0
    for ie, exptname in enumerate(exptList):

        startTime = datetime.datetime.now()
        print 'mglTop_visit_ADV: %s starting %s' % (exptname,startTime.strftime("%y%m%d %H:%M:%S"))

        exptPath = ADV_topDir+'/'+exptname
        print 'mglTop_visit_ADV: exptPath=',exptPath
        outPath = outdir+'/'+exptname
        
        if verbose:
            print ' *',ie,exptPath
            
        try:
            tst = open(outPath+'/tst.csv','w')
        except:
            print 'mglTop_visit_ADV: creating ExptOutput directory', (outPath)
            os.makedirs(outPath)
        tocf = outPath+'/ADV_toc.csv'
        tocs = open(tocf,'w')
        #tocs.write('NTGZ,Data,Path\n')
        tocs.write('Experiment, Batch, Data, Path\n')

        try:
            tst = open(outPath+'/summ/tst.csv','w')
        except:
            print 'mglTop_visit_ADV: creating summ directory',outPath+'/summ'
            os.makedirs(outPath+'/summ')
        try:
            tst = open(outPath+'/inter/tst.csv','w')
        except:
            print 'mglTop_visit_ADV: creating inter directory',outPath+'/inter'
            os.makedirs(outPath+'/inter')

        batchTbl = {}

        exptSubList = glob.glob(exptPath+'/Results_*')   # Results_* level dirs containing
#                                                     FAHV_<rec>_<batch_num>_processed.tgz files
        print 'mglTop_visit_ADV: NSubExperiments=',len(exptSubList)
        for ise, exptSubPath in enumerate(exptSubList):
            if verbose:
                print ' **',ie,ise,exptSubPath
            # dns - get receptor
            resdir=os.path.split(exptSubPath)[1]
            #receptor=resdir.lstrip('Results_')
            receptor=resdir[len('Results_'):]
            # dns - get receptor
            tgzList = glob.glob(exptSubPath+'/*.tgz') 
            for jt,tgzPath in enumerate(tgzList):
                if recon and jt > 0:
                    print 'mglTop_visit_ADV: Recon-only; break'
                    break

                tgznow = os.path.split(tgzPath)[1]
                mpath = ADbatchREPat.match(tgznow)
                if mpath:
                    (x, vinarec, vinabatch) = mpath.groups()
                else:
                    print 'mglTop_visit_ADV: bad match?!',tgznow
                    continue
                batchNo = int(vinabatch)
                if verbose:
                    print 'Attempting to analyze',tgznow 
                                    
                # process all enhanced pdbqt files in the processed batch file: ...
                #
                nparse = visitRpt_ADV_tgz(tgzPath,recon,batchTbl,outdir,tocs,exptname,batchNo,verbose,receptor)
                #
                totParse += nparse
                
        endTime = datetime.datetime.now()
        elapTime = endTime-startTime
        print 'mglTop_visit_ADV: %s done. TotParse=%d NSec=%d' % (exptname,totParse,elapTime.seconds)
            
        tocs.close() # for each experiment directory
        
    print 'mglTop_visit_ADV: TotParse=',totParse

## mgl3 crawl of AD                                                                                                                                          
# import socket
# if socket.gethostname() == 'mgl0':
#     print 'running on mgl0, good!'
#     ADV_topDir = '/export/wcg/processed/'
#     outdir = '/export/wcg/crawl/test/'
#
# elif socket.gethostname() == 'mgl3':
#     print 'running on mgl3, slow(:'
#     ADV_topDir = '/mgl/storage/wcg/processed/'
#     outdir = '/mgl/storage/wcg/crawl/test/'
#
# AD_topDir = '/Data/sharedData/coevol-HIV/WCG/subsets/FAHV_tst_140829_2/'
# outdir = '/Data/sharedData/coevol-HIV/WCG/summRpts/tst/FAHV_140829/'
# exptList = ['Exp81','Exp82', 'Exp84'] # CB, AS, MB; smallest
#
# mglTop_visit_ADV(ADV_topDir, outdir, exptList)

# arg string ala:
# 140905
# /mgl/storage/wcg/processed/ /mgl/storage/wcg/crawl/test/  --exptList "['Exp72']" --verbose
# 140906
# /mgl/storage/wcg/processed/ /mgl/storage/wcg/crawl/test/  --exptList "# arg string ala:
# 140905
# /export/wcg/processed/ /export/wcg/crawl/test/  --exptList "['Exp81','Exp82','Exp84']" --verbose

parser = argparse.ArgumentParser(description='crawl_ADV arguments')
parser.add_argument('ADV_topDir',type=str,help='Path to crawling rootdir')
parser.add_argument('outDir',type=str,help='Path to directory to contain result files')
parser.add_argument('--exptListStr', action="store",help='list of subset exptDir to crawl(string)')
parser.add_argument("--verbose",  action="store_true",help="increase output verbosity")
parser.add_argument("--recon",  action="store_true",help="Reconnaissance sniffing only")

if __name__ == '__main__': 
    
    args, unknown = parser.parse_known_args()
    if args.verbose:
        print 'crawl_ADV: arguments'
        # NB: args is a Namespace object; 
        argsDict = vars(args)
        for k,v in argsDict.items():
            print '\t%s = %s' % (k,v)
    
    if len(unknown)>0:
        print 'crawl_ADV: huh?! Unkown arguments=', unknown
        assert False # can't do break or return here!
    
    if args.exptListStr:
        exptList = eval(args.exptListStr)
    else:
        exptList = None
        
    # print '# PROFILING run!!'
    # import cProfile
    # cProfile.run(('mglTop_visit_ADV("%s","%s",%s,verbose=%s)' % (args.ADV_topDir, args.outDir, exptList, args.verbose)), \
    #              args.outDir+'ADV_mgl0_profile.txt')

    mglTop_visit_ADV(args.ADV_topDir, args.outDir, exptList, verbose=args.verbose)

