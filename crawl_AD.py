''' crawl_AD: utilities to crawl AutoDock FAAH files
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
mode = "lc" # default pose
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

## Shared with ADVina

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

def checkVSresult_AD(lines):
    "parses and validates a PDBQT+ file (lines)"
    try:
        if len(lines[0]) != 0: 
            if lines[0].startswith("USER    ADVS_result"):
                return True
            else:
                return False
        else:
            return False
    except IndexError:
        return False

def setKwMode_AD(mode = "lc"):
    # mode = "le", "lc", "any"
    if mode == "le":
        kw = "AD_LE"
    elif mode == "lc":
        kw = "AD_LC"
    elif mode == "any":
        kw = "AD_L."
    return kw

def getResultCount_AD(lines):
    return int(lines[4].split("AD_results>")[1].strip())

def getRawEnergyData_AD(lines, mode):
    # mode = "le", "lc", "any"
    # format: { "e" : [ float(e)] , "leff" : [float(leff)], "c_size" : [int(c_size)], "c_pc" : [float(c_pc)] }

    kw = setKwMode_AD(mode)+">"
    result = { "e" : [],
                "leff" : [],
                "c_size": [],
                "c_pc" : [] }
    for l in lines:
        if re.search(kw, l):
            l = l.split(">", 1)[1]
            e, leff, c_size, c_pc = l.split(",")
            result['e'].append(float(e))
            result["leff"].append(float(leff))
            result["c_size"].append(int(c_size))
            result["c_pc"].append(float(c_pc))
            if not mode == "any":
                break
    return result

def getLigInteractions_AD(lines, mode):
    kw = setKwMode_AD(mode) #
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

def getLigSource_AD(lines, mode):
    if mode=='lc':
        srcPrefix = 'USER    AD_LC_source> '
    else:
        srcPrefix = 'USER    AD_LE_source> '
    src = ''
    for l in lines:
        if l.startswith(srcPrefix):
            src = l[len(srcPrefix):].strip()
            return src
    return src

def getGenericData_AD(lines):
    receptNamePrefix = 'USER    AD_rec> '
    nresultPrefix = 'USER    AD_results> '
    rname = ''
    nresult = 0
    for l in lines:
        if l.startswith(receptNamePrefix):
            rname = l[len(receptNamePrefix):].strip()
        if l.find(nresultPrefix) != -1:
            nresult = int(l[len(nresultPrefix):].strip())

    return (rname,nresult)

def parseADPDBQT_AD(f):
    ligand = getLines(f)

    if not checkVSresult_AD(ligand):
        return None
            
    ligData = {}
    rname,nresult = getGenericData_AD(ligand)

    if rname=='':
        print 'parseADPDBQT_AD: missing receptor name?!',f
        ligData['recept'] = ''
    else:
        ligData['recept'] = rname

    if nresult==0:
        print 'parseADPDBQT_AD: missing results?!',f
        ligData['nresult'] = 0
        return None
    else:
        ligData['nresult'] = nresult

    ## definitely want at least one result, use LEAST ENERGY
    src = getLigSource_AD(ligand, 'le')
    if src=='':
        print 'parseADPDBQT_AD: missing src?!',f
        ligData['nresult'] = 0
    else:
        ligData['src'] = src

    ligdataRaw = getRawEnergyData_AD(ligand, 'le')
    # dict: {'c_pc': [53.45], 'e': [-6.19], 'leff': [-0.413], 'c_size': [93]}
    for k,v in ligdataRaw.items():
        ligData[k] = v[0]

    liginteract = getLigInteractions_AD(ligand, 'le') #changed from lc \dns
    reducedInterDict = reducePlusInterDict(liginteract)
    ligData.update(reducedInterDict)

    if nresult>1:
        '''
        Tried to instantiate data at itype level but this clashes
        with PDBQT+ search.  Currently, lc data is LOST. 
        '''
        src2 = getLigSource_AD(ligand, 'lc')
        if src2=='':
            print 'parseADPDBQT_AD: missing lc src?!',f
            ligData['nresult'] = 1 #bring it back to 1 result
                                   #only other result should be lc
        else:
            ligData['src2'] = src2
          #defined src2 for 'lc' if nresults>1 ==> 'lc' EXISTS \dns

        ligdataRaw2 = getRawEnergyData_AD(ligand, 'lc')
        for k,v in ligdataRaw2.items():
            ligData[k+'2'] = v[0]

        liginteract2 = getLigInteractions_AD(ligand, 'lc')
        reducedInterDict2 = reducePlusInterDict(liginteract2)
        for itype,v in reducedInterDict2.items():
            ligData[itype+'2'] = v
        #ligData.update(reducedInterDict2) #added \dns
      
        return ligData
    else:
        return ligData
    
ADDotRE = r'([^.]+)\.VS\.pdbqt'                     # (with 4 exceptions) \dns
ADDotREPat = re.compile(ADDotRE)
ADBarRE = r'([^.]+)_VS\.pdbqt'
ADBarREPat = re.compile(ADBarRE)

def visit_AD_tgz(tgzPath,exptname,receptor,recon,verbose):
    dataTbl = {}
    # 2do: Py2.7 allows WITH context management! TODO
# with tarfile.open(tgzPath) as subTar:
# with tarfile.open(subTar) as dataDir:
    
    #tmpDir = tempfile.mkdtemp() # not great for garibaldi00 ???
    #tmpDir = os.getcwd()+'/scratchAD'
    tmpDir = 'scratchAD'
    os.mkdir(tmpDir)

    allTar = tarfile.open(tgzPath)
    allTar.extractall(tmpDir)

    dotFilePat = '/*.VS.pdbqt'
    barFilePat = '/*_VS.pdbqt'

    plusFilePat = dotFilePat # preferred
    adPlusREPat = ADDotREPat # preferred
    firstSniff = True

    #procList = glob.glob(tmpDir+'/faah*')
    procList = glob.glob(tmpDir+'/*')
    print len(procList), procList
    
    if verbose:
        print 'visit_AD_tgz: NTGZ=',len(procList)

    currBatchNo ="Unknown"
    for isd, subdir in enumerate(procList):
        # <<< get batchNo \dns 2014-09-04
        #batchNo=int(os.path.split(subdir)[1].lstrip('faah') )
        batchNo=int(os.path.split(subdir)[1][len('faah'):] )
        ssdList = glob.glob(subdir+'/faah*')
        # print 'visit_AD_tgz: NSubSubdir=',len(ssdList), subdir # debug \dns
        for jssd,ssdPath in enumerate(ssdList):
            # There may be csv files in the untarred directory
            # Need to skip these or script dies
            if os.path.isfile(ssdPath):
                # print 'visit_AD_tgz:Interesting file?!',ssdPath
                continue

            ssd = os.path.split(ssdPath)[1]
            
            # e.g., ssd = 'faah16999_ZINC16035263_EN3md07390CTP' :: <subdir>_<ligand>_<receptor>

            #lig_rec=ssd.lstrip(subdir+'_')
            lig_rec=ssd[len(subdir+'_'):]

            #ligand = lig_rec.rstrip('_'+receptor)
            ligand = lig_rec[:-1*len('_'+receptor)]
            #get ligand \dns 2014-09-04
            #print '   >>>Found ligand: %s for receptor: %s in batch: %s' % (ligand, receptor, batchNo) # debug

            expt = exptname # exptname \dns
            if currBatchNo=="Unknown":
                currBatchNo = batchNo
            else:
                assert batchNo == currBatchNo, 'visit_AD_tgz: inconsistent batchno?! %s %s %s %s %s' % \
                    (currBatchNo,batchNo,expt,ligand,subdir)
                
            if firstSniff:
                firstSniff = False
                glb = glob.glob(ssdPath+plusFilePat)
                if len(glb) != 1:
                    glb2 = glob.glob(ssdPath+barFilePat)
                    if len(glb2) == 1:
                        print 'visit_AD_tgz: DOT VS.pdbqt file not found; BAR VS.pdbqt used',batchNo,expt,ligand,subdir
                        plusFilePat = barFilePat
                        adPlusREPat = ADBarREPat
                        glb = glb2
                    else:
                        print 'visit_AD_tgz: Neither DOT nor BAR VS.pdbqt file not found?!',batchNo,expt,ligand,subdir
                        return currBatchNo,dataTbl

            glb = glob.glob(ssdPath+plusFilePat)

            if len(glb) != 1:
                print 'visit_AD_tgz: plusFilePat non-match?!',batchNo,expt,ligand,subdir
                print glob.glob(ssdPath+'/*')
                break
                
            plusF = glb[0]
            plusf = os.path.split(plusF)[1]
            # ZINC16035263.VS.pdbqt
            mplus = adPlusREPat.match(plusf)
            lig2 = mplus.groups()[0]

            if ligand != lig2:
                # lig2 superior, maintains suffix
                # print 'visit_AD_tgz: ligand != lig2?!',ligand,lig2,batchNo,expt,ligand,subdir
                ligand = lig2

            ###-------
            ligDataPlus = parseADPDBQT_AD(plusF)
            ###-------

            if not ligDataPlus:
                print 'visit_AD_tgz: invalid AD file?!',batchNo,expt,ligand,subdir
                continue

            dk = (expt,receptor,ligand)
            if dk in dataTbl:
                print 'visit_AD_tgz: dup dataKey?!',expt,receptor,ligand
                continue

            dataTbl[dk] = ligDataPlus
            if recon:
                print 'visit_AD_tgz: recon-stop',len(dataTbl)
                return currBatchNo, dataTbl

    shutil.rmtree(tmpDir)
    if verbose:
		print 'visit_AD_tgz: done.',len(dataTbl)
      
    return currBatchNo, dataTbl

def rptData_AD(dataTbl,summf,interf,exptname,batchNo):
    '''V1: produce condensed JSON inter file
            [ [Expt,BatchNo,Recept,Lig, [IType,InterDetails] ] ]
    '''
    
    summs = open(summf,'w')
    summs.write('Expt,Batch,Recept,Ligand,E,Eff,Nvdw,Ninter\n')
    
    allInter = []
    for dk in dataTbl:
        (expt,receptor,lig) = dk
        ligData = dataTbl[dk]
        ninter = 0
        nvdw = 0
        for itype in InterTypes:
            if itype in ligData:
                if itype=='vdw': #added inclusion of lc data-unsure if keeping this \dns
                #if itype=='vdw' or itype=='vdw2':
                    nvdw = len(ligData['vdw'])
                    #nvdw = len(ligData['vdw'])+len(ligData['vdw2'])
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
                    #raa = inter[1]
                    #raalet3 = raa[:3]
                    #pos = raa[3:]
                    #if raalet3 in AADict:
                    #    raaLet = AADict[raalet3]
                    #else:
                    #    raaLet = 'X'
                    #inter[1] = raaLet+pos
    
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

def visitRpt_AD_tgz(tgzPath,recon,batchTbl,outdir,tocs,exptname,receptor,batchNo,verbose): 
    ''' get info, place in this table
    	info is extracted from enhanced pdbqt files inside tarball
    '''	

    # exptname, receptor \dns 2014-09-04i
    #batchNo, dataTbl = visit_AD_tgz(tgzPath,exptname, receptor, recon,verbose)
    # next line is a hack
    batchNoX, dataTbl = visit_AD_tgz(tgzPath,exptname, receptor, recon,verbose)
    if recon:
        print 'visitRpt_AD_tgz: Recon-only; no reporting'
        return len(dataTbl)
    if batchNo in batchTbl:
        print 'visitRpt_AD_tgz: dup batches?!', batchNo, "was", batchTbl[batchNo], "now", tgzPath
        return
    else:
        batchTbl[batchNo] = tgzPath

    summf  = outdir+exptname+'/summ/AD_summ_%07d.csv' % (batchNo)
    interf = outdir+exptname+'/inter/AD_inter_%07d.json' % (batchNo)
    rptData_AD(dataTbl,summf,interf,exptname,batchNo)
    
    tocStr = '%s,%d,%d,%s' % (exptname,batchNo,len(dataTbl),tgzPath)
    if verbose:
        print 'visitRpt_AD_tgz toc:',tocStr
            
    tocs.write(tocStr+'\n')
    # fun2watch! toc
    tocs.flush(); os.fsync(tocs.fileno())

    return len(dataTbl)
        
def mglTop_visit_AD(AD_topDir,outdir,exptList=None,recon=False,verbose=False):
    'recon stops after opening, parsing one file in each tgz'

    if exptList:
        print 'mglTop_visit_AD: Explicit experiment list %s' % (str(exptList))
    else:
        crawlPat = AD_topDir+'/Exp*'
        print 'mglTop_visit_AD: Full crawl of %s' % (crawlPat)
        exptList = [os.path.split(exptPath)[1] for exptPath in glob.glob(crawlPat) ]
 
    print 'mglTop_visit_AD: NExperiments=',len(exptList)

    if verbose:
        print 'mglTop_visit_AD: **Verbose output'

    if recon:
        print 'mglTop_visit_AD: **Reconnaissance sniffing only!'

    totParse = 0
    for ie, exptname in enumerate(exptList):
        
        startTime = datetime.datetime.now()
        print 'mglTop_visit_AD: %s starting %s' % (exptname,startTime.strftime("%y%m%d %H:%M:%S"))
        
        exptPath = AD_topDir+exptname
        outPath = outdir+exptname

        if verbose:
            print ' *',ie,exptPath

        try:
            tst = open(outPath+'/tst.csv','w')
        except:
            print 'mglTop_visit_AD: creating ExptOutput directory', (outPath)
            os.makedirs(outPath)
        tocf = outPath+'/AD_toc.csv'
        tocs = open(tocf,'w')
        tocs.write('Experiment, Batch, Data, Path\n')

        try:
            tst = open(outPath+'/summ/tst.csv','w')
        except:
            print 'mglTop_visit_AD: creating summ directory',outPath+'/summ'
            os.makedirs(outPath+'/summ')
        try:
            tst = open(outPath+'/inter/tst.csv','w')
        except:
            print 'mglTop_visit_AD: creating inter directory',outPath+'/inter'
            os.makedirs(outPath+'/inter')

        batchTbl = {}

	# Results_* level dirs containing FAAH<batch_num>_processed.tgz files

        exptSubList = glob.glob(exptPath+'/Results_*')
        print 'mglTop_visit_AD: exptSubList =',len(exptSubList)
        for jr, receptSub in enumerate(exptSubList):
            #receptor=os.path.split(receptSub)[1].lstrip('Results_')
            receptor=os.path.split(receptSub)[1][len('Results_'):]
            if verbose:
                print ' **',jr,receptor,receptSub
                
            tgzList = glob.glob(receptSub+'/*.tgz')
            print 'sub_mglTop_visit_AD: NTGZ=',len(tgzList)
            for jt,tgzPath in enumerate(tgzList):
                if recon and jt > 0:
                    print 'mglTop_visit_AD: Recon-only; break'
                    break

                tgzFile = os.path.split(tgzPath)[1]
                batchNo = int(tgzFile.split('_')[0])
                # print 'exptPath=%s \nreceptSub=%s \ntgzPath=%s\n' % (exptPath,receptSub,tgzPath)
                # import pdb; pdb.set_trace()
                
                nparse = visitRpt_AD_tgz(tgzPath,recon,batchTbl,outdir,tocs,exptname,receptor,batchNo,verbose) 

                totParse += nparse

        endTime = datetime.datetime.now()
        elapTime = endTime-startTime
        print 'mglTop_visit_AD: %s done. TotParse=%d NSec=%d' % (exptname,totParse,elapTime.seconds)
            
        tocs.close() # for each experiment directory
        
    print 'mglTop_visit_AD: TotParse=',totParse

## mgl crawl of AD
# import socket
# if socket.gethostname() == 'mgl0':
#     print 'running on mgl0, good!'
#     AD_topDir = '/export/wcg/processed/'
#     outdir = '/export/wcg/crawl/test/'

# elif socket.gethostname() == 'mgl3':
#     print 'running on mgl3, slow(:'
#     AD_topDir = '/mgl/storage/wcg/processed/'
#     outdir = '/mgl/storage/wcg/crawl/test/'

# ## hancock
# #AD_topDir = '/Data/sharedData/coevol-HIV/WCG/subsets/FAHV_tst_140829_2/'
# #outdir = '/Data/sharedData/coevol-HIV/WCG/summRpts/tst/FAHV_140829/'
# exptList = ['Exp76', 'Exp78'] #  140906: AS, MB; smallest

# mglTop_visit_AD(AD_topDir, outdir, exptList)

# arg string ala:
# 140905
# /mgl/storage/wcg/processed/ /mgl/storage/wcg/crawl/test/  --exptList "['Exp72']" --verbose

parser = argparse.ArgumentParser(description='crawl_AD arguments')
parser.add_argument('AD_topDir',type=str,help='Path to crawling rootdir')
parser.add_argument('outDir',type=str,help='Path to directory to contain result files')
parser.add_argument('--exptListStr', action="store",help='list of subset exptDir to crawl(string)')
parser.add_argument("--verbose",  action="store_true",help="increase output verbosity")
parser.add_argument("--recon",  action="store_true",help="Reconnaissance sniffing only")

if __name__ == '__main__': 
    
    args, unknown = parser.parse_known_args()
    if args.verbose:
        print 'crawl_AD: arguments'
        # NB: args is a Namespace object; 
        argsDict = vars(args)
        for k,v in argsDict.items():
            print '\t%s = %s' % (k,v)
    
    if len(unknown)>0:
        print 'crawl_AD: huh?! Unkown arguments=', unknown
        assert False # can't do break or return here!
    
    if args.exptListStr:
        exptList = eval(args.exptListStr)
    else:
        exptList = None

    # print '# PROFILING run!!'
    # import cProfile
    # cProfile.run(('mglTop_visit_AD("%s","%s",%s,verbose=%s)' % (args.AD_topDir, args.outDir, exptList, args.verbose)), \
    #              args.outDir+'AD_mgl3_profile.txt')

    mglTop_visit_AD(args.AD_topDir, args.outDir, exptList, verbose=args.verbose)
        
