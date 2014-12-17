''' batchreceptor: utilities to search batchreceptor.csv

    a file located at

        mgl0:/export/wcg_permanentARCHIVE/target_info_adANDvina/

        bstart,bend,receptor,protein,site,library,experiment,
        45254,45488,x4I7G_RT_NNRTIadj_wNNRTI.pdbqt,RT,NNRTIadj,EN,42,
        45489,45723,x4I7G_RT_NNRTIadj.pdbqt,RT,NNRTIadj,EN,42,
        45724,45755,x4I7G_RT_NNRTIadj_wNNRTI.pdbqt,RT,NNRTIadj,NF,43,
        45756,45787,x4I7G_RT_NNRTIadj.pdbqt,RT,NNRTIadj,NF,43,

        The primary routine is:

    unknown...

    At the least, when a batchnumber is used as input, corresponding
    information should be returned:

         - Experiment Number
         - Receptor Name
         - Library (via key/code; e.g., NF = Full NCI Plated Set)
         - Protein (PR, RT, IN, ?)
         - Site (exo, 1F1, LEDGF, KNUC, etc.)

    Notes:

    - Raccoon routines used for parsing pdbqt files
    - variation in _VS.pdbqt and .VS.pdbqt formats handled
    - written with traversal of ADVina batches in mind, but this has not been tested
        - v1.1.1 created from v1.1 with intent to make AD crawl work with 'older'
          processed FAAH AD files; dsantiag@scripps.edu; begin 27 JAN 14
        - Modified mglTop_visit_AD to handle directory structure of processed files
          such that AD_topDir should have processed files in directories with prefix
          "Exp" followed by experiment number (e.g., Exp47), and in those directories
           should be sub-directories with prefix "Results_' followed by receptor*.
           *This may not be unique, so not a good idea to get receptor information here.

          AD_topDir
          |
          -->Exp41
             |
             -->Results_<receptor>
                |
                -->[variable number of [batch number]_processed.tgz files]

        - currently, AD crawl works except for vdw and int
          need to fix le, lc modes; specifically the timing
          mode 'le' relatively works because half the function uses mode 'lc'
          where the errors exist
        - Handles receptor names in the sub(-sub?-)directory beginning with
          letters x (99.999%), E (exception 1), W (exception 2), and G (exception 3).
        - Experiment name/label is reported (e.g., "Exp47").
        - parseADPDBQT now only deals with mode 'le' as opposed to 'lc'
          [least energy and largest cluster, respectively]
        - Possibly fixed out-of-index error, which seemed to stem from absence of
          *VS.pdbqt files.  (Actually might handle both absence of file and empty file;
          file = enhanced pdbqt)
        - visit_AD_tgz now prints out "subdir" for debugging purposes (to know what batch
          is being processed if an error occurs)
        - The newer protocol outputs a summary file *.LOG.csv with directories,
          so visit_AD_tgz now checks for '.' and ignores these files (or directories).
        * last modified 05 FEB 2014

@version 1
@date on 06 Feb 14
@author: dsantiag@scripps.edu (with code from rbelew@ucsd.edu's get_ADInfo.py)
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
from operator import itemgetter

# from AutoDockTools.HelperFunctionsN3P import pathToList, getLines, percent

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
        if len(lines[0]) != 0: # debug \dns --handle finding no *VS.pdbqt
            if lines[0].startswith("USER    ADVS_result"):
                return True 
            else:
                return False
        else:
            return False
    except IndexError:
        return False

def checkVSresult_ADV(lines):
    "parses and validates a PDBQT+ file (lines)"
    if lines[0].startswith("USER ADVS_Vina_result>"):
        return True
    else:
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

def setKwMode_ADV(mode = "1"):
    # USER ADVina_pose1> -10.200, -0.309
    # mode = "1", "2", "..."
    if mode == "any":
        kw = "ADVina_pose."
    else:
        kw = "ADVina_pose"+mode
    return kw

def getResultCount_AD(lines):
    return int(lines[4].split("AD_results>")[1].strip())
def getResultCount_ADV(lines):
    return int(lines[4].split("ADVina_results>")[1].strip())
    
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

def getLigSource_ADV(lines, mode):
    srcPrefix = 'USER ADVina_pose'
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

def getGenericData_ADV(lines):
    receptNamePrefix = 'USER ADVina_rec> '
    nresultPrefix = 'USER ADVina_results> '
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
    if checkVSresult_AD(ligand):
            
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
        return None

def parseADPDBQT_ADV(f,mode='1'):
    ligand = getLines(f)
    if checkVSresult_ADV(ligand):

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
            
        ## definitely want at least one result, use LEAST ENERGY
        src = getLigSource_ADV(ligand, 'le')
        if src=='':
            print 'parseADPDBQT_ADV: missing src?!',f
            ligData['nresult'] = 0
        else:
            ligData['src'] = src
        
        ligdataRaw = getRawEnergyData_ADV(ligand, mode)
        # dict: {'c_pc': [53.45], 'e': [-6.19], 'leff': [-0.413], 'c_size': [93]}

        for k,v in ligdataRaw.items():
            ligData[k] = v[0]
        liginteract = getLigInteractions_ADV(ligand)
        reducedInterDict = reducePlusInterDict(liginteract)
        ligData.update(reducedInterDict)
            
        # 2do: get second pose from ADV?
                       
        return ligData
    else:
        return None

# faah16999_ZINC16035263_EN3md07390CTP
#ADPathRE = r'faah([0-9]+)_([^_]+)_([^/]+)'
#faah22627_zinc_38192659_xmdEq_2R5P1c               #<=="New Player" in town; NOTE ZINC format!
ADPathRE = r'faah([0-9]+)_(ZINC[_0-9]+.*)_(x[^/]+)' # This assumes all ligands are
ADPathREPat = re.compile(ADPathRE, re.IGNORECASE)   # of the format (ZINC[0-9]+.*)
# ZINC16035263.VS.pdbqt                             # and all receptors start with 'x'
ADDotRE = r'([^.]+)\.VS\.pdbqt'                     # (with 2 exceptions) \dns
ADDotREPat = re.compile(ADDotRE)
ADBarRE = r'([^.]+)_VS\.pdbqt'
ADBarREPat = re.compile(ADBarRE)

def visit_AD_tgz(tgzPath,exptname,recon=False):

    dataTbl = {}
    
    tmpDir = tempfile.mkdtemp()
    allTar = tarfile.open(tgzPath)
    allTar.extractall(tmpDir)
    sdList = glob.glob(tmpDir+'/faah*')
    firstSniff = True
    dotFilePat = '/*.VS.pdbqt'
    barFilePat = '/*_VS.pdbqt'
    
    plusFilePat = dotFilePat # preferred
    adPlusREPat = ADDotREPat # preferred
    
    print 'visit_AD_tgz: NSubdir=',len(sdList)
    currBatchNo ="Unkown"
    for isd, subdir in enumerate(sdList):
        ssdList = glob.glob(subdir+'/faah*')
        print 'visit_AD_tgz: NSubSubdir=',len(ssdList), subdir # debug \dns
        for jssd,ssdPath in enumerate(ssdList):
            ssd = os.path.split(ssdPath)[1]
            # faah16999_ZINC16035263_EN3md07390CTP
            ADPathRE = r'faah([0-9]+)_(ZINC[_0-9]+.*)_(x[^/]+)'
            ADPathREPat = re.compile(ADPathRE, re.IGNORECASE)
            mpath = ADPathREPat.match(ssd)
            if ssd.find('.') != -1:
                print 'Interesting file: ',ssdPath # debug \dns
            # There may be csv files in the untarred directory
            # Need to skip these or script dies
            else:   # not a file; a directory! \dns
                mpath = ADPathREPat.match(ssd) # ADPathRE = r'faah([0-9]+)_(ZINC[0-9]+.*)_(x[^/]+)' This will FAIL for 2 exceptions:
                if mpath == None: # did not find x*.pdbqt; try E*.pdbqt OR W*.pdbqt
                    ADPathRE = r'faah([0-9]+)_(ZINC[_0-9]+.*)_(E[^/]+)'
                    ADPathREPat = re.compile(ADPathRE, re.IGNORECASE)
                    mpath = ADPathREPat.match(ssd)
                    print 'Standard receptor filename x*.pdbqt not found; trying E*.pdbqt in ', ssd
                    if mpath == None:
                        ADPathRE = r'faah([0-9]+)_(ZINC[_0-9]+.*)_(G[^/]+)'
                        ADPathREPat = re.compile(ADPathRE, re.IGNORECASE)
                        mpath = ADPathREPat.match(ssd)
                        print 'Filename E*.pdbqt not found; trying G*.pdbqt in ', ssd
                        if mpath == None:
                            ADPathRE = r'faah([0-9]+)_(ZINC[_0-9]+.*)_(W[^/]+)'
                            ADPathREPat = re.compile(ADPathRE, re.IGNORECASE)
                            mpath = ADPathREPat.match(ssd)
                            print 'Neither of x*.pdbqt, E*.pdbqt, or G*.pdbqt not found; trying W*.pdbqt in ', ssd
                            if mpath == None:
                                print 'Neither of x/E/G/W*.pdbqt found for receptor; try something else in ', ssd
                (batchNo,ligand,expt) = mpath.groups()
                expt = exptname # exptname \dns
                if currBatchNo=="Unkown":
                    currBatchNo = batchNo
                else:
                    assert batchNo == currBatchNo, 'visit_AD_tgz: inconsistent batchno?! %s %s %s %s %s' % \
                        (currBatchNo,batchNo,expt,ligand,subdir)
                
                glb = glob.glob(ssdPath+plusFilePat)
                
                if len(glb) != 1:
                    if firstSniff:
                        glb2 = glob.glob(ssdPath+barFilePat)
                        if len(glb2) == 1:
                            print 'visit_AD_tgz: DOT VS.pdbqt file not found; BAR VS.pdbqt used',batchNo,expt,ligand,subdir
                            plusFilePat = barFilePat
                            adPlusREPat = ADBarREPat
                            glb = glb2
                            firstSniff = False
                        else:
                            print 'visit_AD_tgz: Neither DOT nor BAR VS.pdbqt file not found?!',batchNo,expt,ligand,subdir
                            return currBatchNo,dataTbl
                    else:
                        print 'visit_AD_tgz: plusFilePat non-match, not firstSniff?!',batchNo,expt,ligand,subdir
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
                
                dk = (expt,ligand)
                if dk in dataTbl:
                    print 'visit_AD_tgz: dup dataKey?!',expt,ligand
                    continue
                
                dataTbl[dk] = ligDataPlus
                if recon:
                    print 'visit_AD_tgz: recon-stop',len(dataTbl)
                    return currBatchNo, dataTbl

    shutil.rmtree(tmpDir)
    # print 'visit_AD_tgz: done.',len(dataTbl)
      
    return currBatchNo, dataTbl

# fahv.x3AO1_IN_FBP_ZINC05440396_826063109_out_Vina_VS.pdbqt
ADVPathRE = r'fahv\.(.+)_([^_]+)_([0-9]+)_out_Vina(_|\.)VS\.pdbqt'
ADVPathREPat = re.compile(ADVPathRE)

# fahv.x4I7G_RT_NNRTIadj_wNNRTI_ZINC58421065_1_649284996_out_Vina_VS.pdbqt
# ADVBarREZinc = r'fahv\.(x?)(\w+)_([_A-Za-z]+)_(ZINC[0-9]+)_([0-9]+)_([0-9]+)_out_Vina_VS\.pdbqt'
ADVBarREZinc = r'fahv\.(x?)([A-Z0-9]+)_([A-Z]+)_([A-Za-z]+)(_w[A-Z]+I)?_(ZINC[0-9]+)_(\d)_(\d+)_out_Vina_VS\.pdbqt'
ADVBarREZincPat = re.compile(ADVBarREZinc)
# ADVBarREOther = r'fahv\.(x?)(.+)_([_A-Za-z]+)_(.+)_([0-9]+)_out_Vina_VS\.pdbqt'
ADVBarREOther = r'fahv\.(x?)([A-Z0-9]+)_([A-Z]+)_([A-Za-z]+)(_w[A-Z]+I)?_(\w+)_(\d+)_out_Vina_VS\.pdbqt'
ADVBarREOtherPat = re.compile(ADVBarREOther)

def visit_ADV_tgz(tgzPath,recon):

    dataTbl = {}
    
    dataTbl = {}
    # 2do: Py2.7 allows WITH context management!
# with tarfile.open(tgzPath) as subTar:
# with tarfile.open(subTar) as dataDir:

    tmpDir = tempfile.mkdtemp()
    allTar = tarfile.open(tgzPath)
    allTar.extractall(tmpDir)

    # ASSUME: _VS "bar" style processed file names for ADV
    # fahv.x4I7G_RT_NNRTIadj_wNNRTI_ZINC58421065_1_649284996_out_Vina_VS.pdbqt
    procList = glob.glob(tmpDir+'/FAHV*/fahv.*_out_Vina_VS.pdbqt')
    print 'visit_ADV_tgz: NTGZ=',len(procList)
        
    for it,procPath in enumerate(procList):
        procf = os.path.split(procPath)[1]
        
        # ASSUME most ligands are ZINCIDs
        zincLig = True
        mpath = ADVBarREZincPat.match(procf)
        if mpath:
            (x,pdb,prot,bsite,olig,ligand,ligVar,workNo) = mpath.groups()
        else:
            zincLig = False
            mpath = ADVBarREOtherPat.match(procf)
            if not mpath:
                print 'visit_ADV_tgz: very odd proc file name',procf
                continue
            
            (x,pdb,prot,bsite,olig,ligand,workNo) = mpath.groups()
            ligVar = ''

        # the current regexp do not provide perfect results:
        # ADVBarREZincPat produces:
        # ('x', '4I7G_RT_NNRTIadj', 'wNNRTI', 'ZINC58421065', '1', '649284996')
        # ADVBarREOtherPat produces
        # ('x', '4I7G_RT_NNRTIadj_wNNRTI_1CJfrag_x4I7G', 'NNRTIadj', 'RANDOM', '843666400')

        if olig:
            olig = olig[2:] # drop '_w'

        ###-------
        ligData = parseADPDBQT_ADV(procPath)
        ###-------
        
        if not(ligData):
            print 'visit_ADV_tgz: invalid ADV file?!',procf
            continue

        ligData['workNo'] = int(workNo)

        dk = (pdb,bsite,ligand,ligVar,olig)
        
        if dk in dataTbl:
            print 'visit_ADV_tgz: dup dataKey?!',dk
            continue

        dataTbl[dk] = ligData

                                
    shutil.rmtree(tmpDir)
    # print 'visit_ADV_tgz: done.',len(dataTbl)
    
    return dataTbl

def rptData_ADV(dataTbl,outs,inters):
    # print 'Expt,Recept,Ligand,E,Eff,Nvdw,Ninter'
    for dk in dataTbl:
        (pdb,bsite,lig,ligVar,olig) = dk
        expt = pdb+'_'+bsite
        if len(ligVar)>0:
            lig = lig +'_'+ligVar
        ligData = dataTbl[dk]
        ninter = 0
        nvdw = 0
        for itype in InterTypes:
            if itype in ligData:
                if itype=='vdw':
                    nvdw = len(ligData['vdw'])
                else:
                    ninter += len(ligData[itype])
        
        outs.write('%s,%s,%s,%s,%s,%d,%d\n' % \
                   (expt,ligData['recept'],lig,ligData['e'],ligData['leff'],nvdw,ninter))
        
        # Expt,Recept,Lig,IType,Liname,Rchain,Raa,Ratom
        for itype in InterTypes:
            if itype in ligData:
                for inter in ligData[itype]:
                    if itype=='vdw':
                        (rchain,raa,ratom) = inter
                        liname = ''
                    elif itype=='ppi' or itype=='tpi':
                        (rchain,raa,rcenter,ligcenter) = inter
                        liname = ''
                        ratom = ''
                    else:
                        (liname,rchain,raa,ratom) = inter
                    inters.write('%s,%s,%s,%s,%s,%s,%s,%s\n' % (expt,ligData['recept'],lig,itype,liname,rchain,raa,ratom))

def dock2DB_ADV(dataTbl,connect):
    # conn = psycopg2.connect('dbname=django user=postgres password=PW host=/tmp/')
    curs = connect.cursor()
    
    # psycopog2 syntax
    # cur.execute("INSERT INTO test (num, data) VALUES (%s, %s)", (100, "abc'def"))
    
    for dk in dataTbl:
        (pdb,bsite,lig,ligVar,olig) = dk
        expt = pdb+'_'+bsite
        if len(ligVar)>0:
            lig = lig +'_'+ligVar
        ligData = dataTbl[dk]
        ninter = 0
        nvdw = 0
        for itype in InterTypes:
            if itype in ligData:
                if itype=='vdw':
                    nvdw = len(ligData['vdw'])
                else:
                    ninter += len(ligData[itype])
        
        outs.write('%s,%s,%s,%s,%s,%d,%d\n' % \
                   (expt,ligData['recept'],lig,ligData['e'],ligData['leff'],nvdw,ninter))
        
        # Expt,Recept,Lig,IType,Liname,Rchain,Raa,Ratom
        for itype in InterTypes:
            if itype in ligData:
                for inter in ligData[itype]:
                    if itype=='vdw':
                        (rchain,raa,ratom) = inter
                        liname = ''
                    elif itype=='ppi' or itype=='tpi':
                        (rchain,raa,rcenter,ligcenter) = inter
                        liname = ''
                        ratom = ''
                    else:
                        (liname,rchain,raa,ratom) = inter
                    inters.write('%s,%s,%s,%s,%s,%s,%s,%s\n' % (expt,ligData['recept'],lig,itype,liname,rchain,raa,ratom))

def visitRpt_ADV_tgz(ntgz,tgzPath,recon,batchTbl,outdir,tocs):

    
    dataTbl = visit_ADV_tgz(tgzPath,recon)
        
    outf = outdir+'summ/ADV_summ_%05d.csv' % (ntgz)
    outs = open(outf,'w')
    outs.write('Expt,Recept,Ligand,E,Eff,Nvdw,Ninter\n')
    interf = outdir+'inter/ADV_inter_%05d.csv' % (ntgz)
    inters = open(interf,'w')
    inters.write('Expt,Recept,Lig,IType,Liname,Rchain,Raa,Ratom\n')
    rptData_ADV(dataTbl,outs,inters)
    outs.close()
    inters.close()
    tocStr = '%05d,%d,%s' % (ntgz,len(dataTbl),tgzPath)
    print 'mglTop_visit_ADV toc:',tocStr
            
    tocs.write(tocStr+'\n')
    # fun2watch! toc
    tocs.flush(); os.fsync(tocs.fileno())

def visitRpt_SAMPL(ntgz,ligPath,batchTbl,outdir,tocs):
    
    dataTbl = visit_SAMPL(ligPath)
        
    outf = outdir+'summ/ADV_summ_%05d.csv' % (ntgz)
    outs = open(outf,'w')
    outs.write('Expt,Recept,Ligand,E,Eff,Nvdw,Ninter\n')
    interf = outdir+'inter/ADV_inter_%05d.csv' % (ntgz)
    inters = open(interf,'w')
    inters.write('Expt,Recept,Lig,IType,Liname,Rchain,Raa,Ratom\n')
    rptData_ADV(dataTbl,outs,inters)
    outs.close()
    inters.close()
    tocStr = '%05d,%d,%s' % (ntgz,len(dataTbl),ligPath)
    print 'visitRpt_SAMPL toc:',tocStr
            
    tocs.write(tocStr+'\n')
    # fun2watch! toc
    tocs.flush(); os.fsync(tocs.fileno())


InterTypes = ('hba', 'hbd', 'mtl','ppi','tpi','vdw')
#InterTypes = ('hba', 'hbd', 'mtl','ppi','tpi','vdw','hba2','hbd2', 'mtl2','ppi2','tpi2','vdw2')

# d:<0>:O3~~B:ARG57:N
# InterRE = r'd:<([0-9]+)>:([A-Z]+)[0-9]+~~(.*):([A-Z]+[0-9]+):([A-Z]+)'
# InterRE1 = r'd:<([0-9]+)>:([A-Z]+)[0-9]+~~(.*):(.+):(.+)'

# 2do: 19 Oct 13
# new ADV patterns?
# hba: A:1CJ601:O1~~A:GLN182:N

# 27 Nov 13: accept new inter patterns for SAMPL
# N:UNK1:O~~A:THR174:OG1
#InterRE = r'(.+):(.+):([A-Z]+)~~(.*):(.+):(.+)'
InterRE = r'(.+):.+():([A-Z]+[0-9]*)~~(.*):(.+):(.+)'

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
                        rinterDict[itype].append( (latom,rchain,raa,ratom) )
                    except:
                        print 'reducePlusInterDict: bad %s string?! %s' % (itype,inter)
            
    return rinterDict

def rptData_AD(dataTbl,outs,inters,bint):
    # print 'Expt,Recept,Ligand,E,Eff,Nvdw,Ninter'
    for dk in dataTbl:
        (expt,lig) = dk
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
        
        outs.write('%s,%d,%s,%s,%s,%s,%d,%d\n' % \
                   (expt,bint,ligData['recept'],lig,ligData['e'],ligData['leff'],nvdw,ninter))
        
        # Expt,Recept,Lig,IType,Liname,Rchain,Raa,Ratom
        for itype in InterTypes:
            if itype in ligData:
                for inter in ligData[itype]:
                    if itype=='vdw':
                    #if itype=='vdw' or itype=='vdw2': # \dns
                        (rchain,raa,ratom) = inter
                        liname = ''
                    elif itype=='ppi' or itype=='tpi':
                    #elif itype=='ppi' or itype=='tpi' or itype=='ppi2' or itype=='tpi2': # \dns
                        (rchain,raa,rcenter,ligcenter) = inter
                        liname = ''
                        ratom = ''
                    else:
                        (liname,rchain,raa,ratom) = inter
                    inters.write('%s,%d,%s,%s,%s,%s,%s,%s,%s\n' % (expt,bint,ligData['recept'],lig,itype,liname,rchain,raa,ratom))

def visitRpt_AD_tgz(tgzPath,recon,batchTbl,outdir,tocs,exptname): # exptname \dns
    batch, dataTbl = visit_AD_tgz(tgzPath,exptname,recon) # exptname \dns
    bint = int(batch)
    if bint in batchTbl:
        print 'visitRpt_AD_tgz: dup batches?!',bint, "was", batchTbl[bint], "now", tgzPath
        return
    else:
        batchTbl[bint] = tgzPath
        
    outf = outdir+'summ/AD_summ_%05d.csv' % (bint)
    outs = open(outf,'w')
    outs.write('Expt,Recept,Ligand,E,Eff,Nvdw,Ninter\n')
    interf = outdir+'inter/AD_inter_%05d.csv' % (bint)
    inters = open(interf,'w')
    inters.write('Expt,Recept,Lig,IType,Liname,Rchain,Raa,Ratom\n')
    rptData_AD(dataTbl,outs,inters,bint)
    outs.close()
    inters.close()
    tocStr = '%s,%05d,%d,%s' % (exptname,bint,len(dataTbl),tgzPath)
    print 'mglTop_visit_AD toc:',tocStr
            
    tocs.write(tocStr+'\n')
    # fun2watch! toc
    tocs.flush(); os.fsync(tocs.fileno())
        
def mglTop_visit_AD(outdir,recon=False):
    'recon stops after opening, parsing one file in each tgz'
    
    measuredList = glob.glob(AD_topDir+'Exp*')
    print 'mglTop_visit_AD: NMeasured=',len(measuredList)
    tocf = outdir+'AD_toc.csv'
    tocs = open(tocf,'w')
    tocs.write('Experiment,Batch,Data,Path\n')
    
    try:
        tst = open(outdir+'summ/tst.csv','w')
    except:
        'mglTop_visit_AD: creating summ directory',outdir+'/summ'
        os.makedirs(outdir+'summ')
    try:
        tst = open(outdir+'inter/tst.csv','w')
    except:
        'mglTop_visit_AD: creating inter directory',outdir+'/inter'
        os.makedirs(outdir+'inter')
    
    batchTbl = {}
    for ie, kbatchPath in enumerate(measuredList):
        print 'mglTop_visit_AD: *',ie,kbatchPath
        exptname = os.path.split(kbatchPath)[1] # exptname \dns
        sub_measuredList = glob.glob(kbatchPath+'/Results_*')
        print 'sub_mglTop_visit_AD: subNMeasured=',len(sub_measuredList)
        for sub_ie, sub_kbatchPath in enumerate(sub_measuredList):
            tgzList = glob.glob(sub_kbatchPath+'/*.tgz')
            print 'sub_mglTop_visit_AD: NTGZ=',len(tgzList)
            for jt,tgzPath in enumerate(tgzList):
            
                visitRpt_AD_tgz(tgzPath,recon,batchTbl,outdir,tocs,exptname) # exptname \dns
            
    tocs.close()

def mgl_getAD_PDBQT(batchNo,expt,ligand):
    'drill down into processed to retrieve particular PDBQT'
    
    kBatch = batchNo / 1000
    kbs = str(kBatch)
    tgzPath = AD_topDir+kbs+'000s_measured/'+str(batchNo)+'_processed.tgz'
    

    try:
        allTar = tarfile.open(tgzPath)
    except IOError:
        print "mgl_getAD_PDBQT: can't find batch %d file?!", tgzPath
        return None

    tmpDir = tempfile.mkdtemp()
    allTar = tarfile.open(tgzPath)
    allTar.extractall(tmpDir)
    
    sdList = glob.glob(tmpDir+'/faah*')
    subdir = sdList[0]
    # faah16999_ZINC16035263_EN3md07390CTP
    dirName = 'faah%d_%s_%s/' % (batchNo,ligand,expt)
    # import pdb; pdb.set_trace()
    fname = None
    fname1 = subdir+'/'+dirName+'%s.VS.pdbqt' % (ligand)
    fname2 = subdir+'/'+dirName+'%s_VS.pdbqt' % (ligand)
    
    try:
        test = open(subdir+'/'+dirName+fname1)
        fname = fname1
    except IOError:
        try:
            test = open(subdir+'/'+dirName+fname2)
            fname = fname2
        except IOError:
            print "mgl_getAD_PDBQT: can't find either .VS or _VS pdbqt file?!", tgzPath,fname1,fname2
            return None
        
    assert fname != None, 'mgl_getAD_PDBQT: bad logic?!'

    plusf = open(subdir+'/'+dirName+fname)
    plusfs = plusf.read()
    plusf.close()

    shutil.rmtree(tmpDir)
    return (fname,len(plusfs),plusfs)

def mgl_getADV_PDBQT(tgzPath,ligand):
    'drill down into processed to retrieve particular PDBQT'

    try:
        allTar = tarfile.open(tgzPath)
    except IOError:
        print "mgl_getAD_PDBQT: can't find batch %d file?!", tgzPath
        return None

    # /mgl/storage/WCG3/FAAH_Vina/processed/Exp47/Results_x3NF6_B_IN_Y3/FAHV_x3NF6_B_IN_Y3_0047089_processed.tgz
    
    tmpDir = tempfile.mkdtemp()
    allTar = tarfile.open(tgzPath)
    allTar.extractall(tmpDir)

    tgzBits = tgzPath.split('/')
    runName = tgzBits[-2]
    # Results_x3NF6_B_IN_Y3
    # /tmp/tmpoK42yk/FAHV_x3NF6_B_IN_Y3_0047094_processed
    subdir = tgzBits[-1]
    subdir = subdir[:-4]
    fnamePrefix = runName.replace('Results_','fahv.')
    fnpat = tmpDir+'/'+subdir+'/'+fnamePrefix+('_%s_*_out_Vina_VS.pdbqt' % (ligand))
    fnList = glob.glob(fnpat)
    # import pdb; pdb.set_trace()
    fname = fnList[0]
    
    # fahv.x3NF6_B_IN_Y3_ZINC17058311_1096072276_out_Vina_VS.pdbqt
     
    try:
        test = open(fname)
        test.close()
    except IOError:
        print "mgl_getADV_PDBQT: can't find _VS pdbqt file?!", tgzPath,fname
        return None
        
    plusf = open(fname)
    plusfs = plusf.read()
    plusf.close()

    shutil.rmtree(tmpDir)
    fnameBits = fname.split('/')
    fname = fnameBits[-1]
    return (fname,len(plusfs),plusfs)

def getAD_MultPDBQT(plusfList,outDir):
    
    for (batch,expt,ligand) in plusfList:
        bno = int(batch)
        (fname,pfsize,pf) = mgl_getAD_PDBQT(bno,expt,ligand)
        print batch,expt,ligand,fname,pfsize
        outs = open(outDir+fname,'w')
        outs.write(pf)
        outs.close()
        
def getAD_MultPDBQT_file(plusFile,outDir):
    reader = csv.DictReader(open(plusFile))
    # Expt,Batch,Lig
    for i,entry in enumerate(reader):
        expt = entry['Expt']
        batch = entry['Batch']
        ligand = entry['Lig']
        bno = int(batch)
        if runType=='AD':
            (fname,pfsize,pf) = mgl_getAD_PDBQT(bno,expt,ligand)
        else:
            (fname,pfsize,pf) = mgl_getADV_PDBQT(bno,expt,ligand)
        try:
            tst = open(outdir+'%s/' % (expt),'w')
        except:
            print 'getMultPDBQT_file: creating directory',expt
            os.makedirs(outdir+'%s/' % expt)
        print batch,expt,ligand,fname,pfsize
        outs = open(outDir+('%s/' % expt)+fname,'a/')
        outs.write(pf)
        outs.close()

def getADV_MultPDBQT_file(plusFile,outdir):
    reader = csv.DictReader(open(plusFile))
    # Expt,Batch,Lig
    for i,entry in enumerate(reader):
        expt = entry['Expt']
        path = entry['Path']
        ligand = entry['Lig']
        (fname,pfsize,pf) = mgl_getADV_PDBQT(path,ligand)
        try:
            tst = open(outdir+'%s/tst.txt' % (expt),'w')
        except:
            print 'getMultPDBQT_file: creating directory',expt
            os.makedirs(outdir+'%s/' % expt)
        print i,expt,ligand,fname,pfsize
        outs = open(outdir+('%s/' % expt)+fname,'w')
        outs.write(pf)
        outs.close()
    
def mglTop_visit_ADV(ADV_topDir,exptList,outdir,recon=False):
    # exptList = glob.glob(ADV_topDir+'/Exp*')
    print 'mglTop_visit_ADV: NExperiments=',len(exptList)
    
    tocf = outdir+'ADV_toc.csv'
    tocs = open(tocf,'w')
    tocs.write('NTGZ,Data,Path\n')

    try:
        tst = open(outdir+'summ/tst.csv','w')
    except:
        'mglTop_visit_AD: creating summ directory',outdir+'/summ'
        os.makedirs(outdir+'summ')
    try:
        tst = open(outdir+'inter/tst.csv','w')
    except:
        'mglTop_visit_AD: creating inter directory',outdir+'/inter'
        os.makedirs(outdir+'inter')

    batchTbl = {}

    ntgz = 0
    for ie, exptPath in enumerate(exptList):
        print ' *',ie,exptPath

        exptSubList = glob.glob(exptPath+'/Res*')
        print 'mglTop_visit_ADV: NSubExperiments=',len(exptSubList)
        for ise, exptSubPath in enumerate(exptSubList):
            print ' *',ise,exptSubPath

            tgzList = glob.glob(exptSubPath+'/*.tgz')
            print 'mglTop_visit_ADV: NTGZ=',len(tgzList)
            for jt,tgzPath in enumerate(tgzList):
                
                ntgz += 1
                visitRpt_ADV_tgz(ntgz,tgzPath,recon,batchTbl,outdir,tocs)
                
    tocs.close()
    
def top_visit_SAMPL(SAMPL_topDir,outdir):
    exptList = ['LEDGF', 'Y3', 'FBP']
    
    print 'top_visit_SAMPL: NExperiments=',len(exptList)
    
    tocf = outdir+'ADV_toc.csv'
    tocs = open(tocf,'w')
    tocs.write('NTGZ,Data,Path\n')

    try:
        tst = open(outdir+'summ/tst.csv','w')
    except:
        'top_visit_SAMPL: creating summ directory',outdir+'/summ'
        os.makedirs(outdir+'summ')
    try:
        tst = open(outdir+'inter/tst.csv','w')
    except:
        'top_visit_SAMPL: creating inter directory',outdir+'/inter'
        os.makedirs(outdir+'inter')

    batchTbl = {}

    ntgz = 0
    for ie, expt in enumerate(exptList):
        exptPath = SAMPL_topDir+expt+'/'
        print ' *',ie,exptPath

        exptSubList = glob.glob(exptPath+'*')
        print 'top_visit_SAMPL: NRecept=',len(exptSubList)
        for ise, exptSubPath in enumerate(exptSubList):
            print ' *',ise,exptSubPath

            ligList = glob.glob(exptSubPath+'/*')
            print 'top_visit_SAMPL: NLig=',len(ligList)
            for jt,ligPath in enumerate(ligList):
                ligPath += '/'
                ntgz += 1
                visitRpt_SAMPL(ntgz,ligPath,batchTbl,outdir,tocs)
                
    tocs.close()
                
## initial single PDBQT+ file experiments

# WCGDataDir = '/Data/sharedData/coevol-HIV/hivortal/WCG/procData/FAAH_AD2/'
# summRptDir = '/Data/sharedData/coevol-HIV/hivortal/WCG/summRpts/faah_AD2/'

# pdbqtDir = '/Data/sharedData/coevol-HIV/hivortal/lab/ap_expt30_1f1_130220_logs/pdbqt/'
# inf = 'ZINC00031832_VS.pdbqt'
# parseADPDBQT(pdbqtDir+inf)

## Local parse of AD, AD/V
# AD_TGZ_PATH = '/Data/sharedData/coevol-HIV/hivortal/WCG/subsets/16652_processed.tgz'
# ADV_topDir = '/Data/sharedData/coevol-HIV/hivortal/WCG/subsets/FAHV_Proc/'
# outdir = '/Data/sharedData/coevol-HIV/hivortal/WCG/summRpts/tst/FAHV_131018/'
#
# mglTop_visit_ADV(ADV_topDir, outdir)

# tocf = outdir+'AD_toc.csv'
# tocs = open(tocf,'w')

# try:
# tst = open(outdir+'summ/tst.csv','w')
# except:
# 'mglTop_visit_AD: creating summ directory',outdir+'/summ'
# os.makedirs(outdir+'summ')
# try:
# tst = open(outdir+'inter/tst.csv','w')
# except:
# 'mglTop_visit_AD: creating inter directory',outdir+'/inter'
# os.makedirs(outdir+'inter')

# visitRpt_AD_tgz(AD_TGZ_PATH,False,{},outdir, tocs)

# ## profiled version

# # import cProfile
# # import pstats
# # pstatFile = outdir+'parseADPDBQT_AD_profile.txt'
# # print 'saving profile stats to',pstatFile
# # cProfile.run('visitRpt_AD_tgz(AD_TGZ_PATH,False,{},outdir, tocs)',pstatFile)
# # p = pstats.Stats(pstatFile)
# # p.strip_dirs().sort_stats(-1).print_stats()

# tocs.close()


## full runs @ MGL
# AD_topDir = '/mgl/storage/wcg_permanentARCHIVE/processed/'
#AD_topDir = '/mgl/storage/wcg_permanentARCHIVE/processed/'
# ADV_topDir = '/mgl/storage/WCG3/FAAH_Vina/processed/'
# exptList = ['Exp43','Exp45'] #this is obsolete for AD crawl v1.1.1
# outdir = '/home/rik/FAHV_131103/'
#outdir = '/mgl/storage/wcg_permanentARCHIVE/crawl_output/processed_output/'
#mglTop_visit_AD(outdir) # ~line 777
# mglTop_visit_ADV(ADV_topDir,exptList,outdir)


## MGL-based utility

# outdir = '/home/rik/faah_anal/'
# plus2getList = [(8520,'xmdEq_2R5P1c', 'ZINC04476013'), \
# (13083,'xmdEq_2R5P1c', 'ZINC04476013')]
# getMultPDBQT(plus2getList,outdir)

# get Ex47 - ADV

#ADV_topDir = '/mgl/storage/WCG3/FAAH_Vina/processed/'
#outDir = '/home/rik/FAHV_Ex47_best/'
#bestFile = outDir+'bestLig_100.csv'
#getADV_MultPDBQT_file(bestFile,outDir)


# batchreceptor.py

def readBatchReceptor(currentBR):
    infof = open(currentBR)
    infofs = infof.read()
    infof.close()

    dictBR = {}

    byendline = '\n'
    bycomma   = ','

    lines = infofs.split(byendline)
    isfirstline = 1
    for l in lines:
        if isfirstline:
            isfirstline = 0
        else:
            data = l.split(bycomma) # disregard last comma and possible null element
            if len(data)>1:
#('32', 'OT_bb', 'PR', 'ActiveSite', 'xEyeSiteXtl5NI', 'DSTT,faah_ExpandedASite2_Feb2010.gpf,faah_template_EndByGen_March09.dpf,AD')
                bstart = data[0]
                bend   = data[1]
                receptor = data[2]
                protein = data[3]
                site = data[4]
                library = data[5]
                expnum = data[6]
                pdbid = data[7].strip(',\r')
                if len(data) > 8:
                    mygpf = data[8]
                    mydpf = data[9]
                    myprog = data[10].strip('\r')
                keyBR = "%s_%s" % (bstart, bend)
                if len(keyBR)>2:
                    itemBR = (expnum, library, protein, site, receptor, pdbid)
                    #print itemBR
                    dictBR[keyBR] = itemBR

    return dictBR
"""         
        bstart,bend,receptor,protein,site,library,experiment,
        45254,45488,x4I7G_RT_NNRTIadj_wNNRTI.pdbqt,RT,NNRTIadj,EN,42,
        45489,45723,x4I7G_RT_NNRTIadj.pdbqt,RT,NNRTIadj,EN,42,
        45724,45755,x4I7G_RT_NNRTIadj_wNNRTI.pdbqt,RT,NNRTIadj,NF,43,
        45756,45787,x4I7G_RT_NNRTIadj.pdbqt,RT,NNRTIadj,NF,43,
"""
 
def getBRinfo(batchnum, dictBR):
    for keyBR in dictBR.keys():
        value =  keyBR.split('_')
        if int(value[0]) <= int(batchnum) <= int(value[1]):
            return dictBR[keyBR]
    return None

def getBRexpFROMbatch(batchnum, dictBR):
    for keyBR in dictBR.keys():
        value =  keyBR.split('_')
        if int(value[0]) <= int(batchnum) <= int(value[1]):
            batchinfo = dictBR[keyBR]
            thisbatch = batchinfo[0]
            return thisbatch
    return None

def printBRinfo( expnum, batch, lib, prot, site, rec ):
    print '**********************************************************'
    print ' Experiment:     %s' % expnum
    print ' Batch Number:   %s' % batch
    print ' Library Code:   %s' % lib
    print ' Protein Target: %s' % prot
    print ' Target Site:    %s'  % site
    print ' Receptor Name:  %s' % rec
    print '**********************************************************'

def getRecDirFromExp( expnum, dictBR ):
    recDirList = []
    recStartList = []
    recEndList = []
    for keyBR, infoBR in dictBR.iteritems():
        if len(infoBR)>5:
            if infoBR[0] == expnum:
                #print infoBR[0], expnum
                recDirList.append( infoBR[4].rstrip('.pdbqt') )
                recStartList.append( int( keyBR.split('_')[0] ) )
                recEndList.append( int( keyBR.split('_')[1] ) )
    recBatchList = zip( recDirList,recStartList,recEndList )
    return recBatchList


def getTotalBatchesFromExp( expnum, dictBR):
    batchsum = 0
    for keyBR, infoBR in dictBR.iteritems():
        if len(infoBR)==6:
            #if int(infoBR[0]) == int(expnum):
            if infoBR[0] == expnum: # do XXX NOT XXX use int for cases such as "34ext1"
                #print infoBR[0], expnum
                #recDirList.append( infoBR[4].rstrip('.pdbqt') )
                #print keyBR
                keyBRsum = int( keyBR.split('_')[1] ) - int( keyBR.split('_')[0] ) + 1
                batchsum = batchsum+keyBRsum
    return batchsum

#currentBR = '/export/wcg_permanentARCHIVE/target_info_adANDvina/batchreceptor.csv'
currentBR = '/home/dsantiag/batchreceptor.csv'

#querybatch = input('Enter a batch number: ')
mydic = readBatchReceptor(currentBR)
#print mydic
#infoBR = getBRinfo(querybatch, mydic)
#try:
#    if infoBR[4]:
#        print 'Info for %s is %s' % (querybatch,infoBR)
#        printBRinfo(infoBR[0], querybatch, infoBR[1], infoBR[2], infoBR[3], infoBR[4])
#except:
#    print 'Incorrect batchnumber:', querybatch
if len(sys.argv) > 1:
    queryRecExp = sys.argv[1]
else:
    sys.exit("Please provide an experiment number.")
    queryRecExp = 105
#myRecList = getRecDirFromExp(queryRecExp, mydic)
#print myRecList

crawldir='/export/wcg/crawl/Exp%s/' % queryRecExp
datadir ='/export/wcg/crawl/data/Exp%s/' % queryRecExp

try:
    tst = open(datadir+'tst.csv','w')
    os.remove( datadir+'tst.csv'  )
except:
    'batchreceptor.py: creating summ directory',datadir
    os.makedirs(datadir)


#crawldir='/export/wcg_permanentARCHIVE/crawl_output/processed2_output'
#crawldir='/export/wcg_permanentARCHIVE/crawl_output/processed_output'
#crawldir='/export/wcg_permanentARCHIVE/crawl_output/processed_output_archive1'

#myanswer = getBRinfo(queryRecExp, mydic)
#myanswer = getBRexpFROMbatch(queryRecExp, mydic)
#myanswer = getTotalBatchesFromExp(queryRecExp, mydic)
myanswer = getRecDirFromExp( queryRecExp, mydic )
#print myanswer

#sys.exit()

#answerstr = myanswer[0]
#isfirst=1
#for i in range( len(myanswer) ):
#    if isfirst:
#        isfirst=0
#    else:
#        answerstr = answerstr+'\n'+myanswer[i]
#print answerstr

#print "DIRECTORY TO INSPECT: %s" % crawldir
interdir = crawldir+'inter/'
interList = glob.glob(interdir+'/*.csv')
summdir  = crawldir+'summ/'
summList  = glob.glob(summdir +'/*.csv')

print 'Starting big loop for Exp. %s.' % queryRecExp
print 'The size of myanswer is %d.' % len( myanswer )

for cnt,info in enumerate(myanswer):
    print 'LOOP: %d' % cnt
    masterdatatuple = []
    #print info[0]
    recname = info[0]
    print recname
    #datlinecount = 0
    #outdataf = datadir+queryRecExp+'_'+info[0]+'.csv'
    #outvalsf = datadir+queryRecExp+'_'+info[0]+'.dat'
    #outvalss = open(outvalsf, 'w')
    #outdatas = open(outdataf,"w")
    #datatuple=[]
    #print "FILE TO BE GENERATED: %s" % ( outdataf )
    brange = int( info[2] ) - int( info[1] ) + 1
    for bnum in range( brange ):
        batchnum = info[1]+bnum
        #print recname,batchnum
        #print str( batchnum )
        #datatuple=[]    # populate this list with tuples from matching batchnumbers per receptor
        for fileitem in summList:
            summfile = os.path.split(fileitem)[1]
            #print summfile
            if re.search( str(batchnum),summfile ):

                datatuple=[]    # populate this list with tuples from matching batchnumbers per receptor

                #print batchnum,summfile
                f=open(fileitem,"r")
                finfo = f.readlines()
                f.close()
                #print summfile,len(finfo)
                linecount = 0
                for line in finfo:
                     if linecount:
                         # code
                         #print line
                         nowscore = float( line.split(',')[4] )
                         nowlef   = float( line.split(',')[5] )
                         nowlig   =        line.split(',')[3]
                         nowbatch = int(   line.split(',')[1] )
                         nowVdw   = int(   line.split(',')[6] )
                         nowInter   = int(   line.split(',')[7] )
                         nowtuple=( nowscore, nowlef, nowlig, nowbatch, nowVdw, nowInter )
                         #nowvals = '%f0.2,%0.3f\n' % ( nowscore,nowlef )
                         #outvalss.write( nowvals )
                         #print nowtuple
                         #datatuple.append( nowtuple )
                         masterdatatuple.append( nowtuple )
                         #sorted( datatuple, key=itemgetter(1) )
                         #sorted( datatuple, key=itemgetter(0) )
                         #print datatuple
                     else:
                         linecount = 1
                #print batchnum, datatuple[0]
                #datatuple = sorted( datatuple, key=itemgetter(1) )
                
                #print datatuple[0]
                #datatuple = sorted( datatuple, key=itemgetter(0) )

                masterdatatuple = sorted( masterdatatuple, key=itemgetter(1) )
                masterdatatuple = sorted( masterdatatuple, key=itemgetter(0) )

                #datlinecount = 0
                #outsubdataf = '%s%s_%s_%d.csv' % ( datadir,queryRecExp,recname,batchnum )
                #print "FILE TO BE GENERATED: %s" % ( outsubdataf )
                #outsubdatas = open(outsubdataf,"w")
                #print "WRITING TO: %s" % outsubdataf
                #print 'Batch: %d\tCurrent: %d\tMaster: %d' % ( batchnum,len(datatuple),len(masterdatatuple) )
                #if len( datatuple ) < 550:
                #    maxwhile = len( datatuple )
                #else:
                #    maxwhile = 550
                #while datlinecount<maxwhile:
                #    nowscore   =datatuple[datlinecount][0]
                #    nowlef     =datatuple[datlinecount][1]
                #    nowlig     =datatuple[datlinecount][2]
                #    nowbatch   =datatuple[datlinecount][3]
                #    newdatstr = '%0.1f,%0.3f,%s,%s\n' % ( nowscore,nowlef,nowlig,nowbatch )
                    #print "DATA: %s" % newdatstr
                #    outsubdatas.write( newdatstr )
                #    datlinecount = datlinecount+1
                #outsubdatas.close()

                #print datatuple[0]
    print 'Please wait.  Now sorting the Master Data List for %s.' % recname
    print 'The size of the Master is %d.' % len( masterdatatuple )
    #masterdatatuple = sorted( masterdatatuple, key=itemgetter(1) )
    #masterdatatuple = sorted( masterdatatuple, key=itemgetter(0) )
    masterdatatuple.sort( key=itemgetter(0) )

    # print to file
    outdataf = datadir+queryRecExp+'_'+recname+'.csv'
    outdatas = open(outdataf,"w")
    #ourvalss.close()
    datlinecount = 0
    print "WRITING TO: %s" % outdataf
    mymax = len( masterdatatuple )
    if len( masterdatatuple ) < mymax:
        maxwhile = len( masterdatatuple )
    else:
        maxwhile = mymax
    while datlinecount<maxwhile:
        # nowtuple=( nowscore, nowlef, nowlig, nowbatch, nowVdw, nowInter )
        nowscore   =masterdatatuple[datlinecount][0]
        nowlef     =masterdatatuple[datlinecount][1]
        nowlig     =masterdatatuple[datlinecount][2]
        nowbatch   =masterdatatuple[datlinecount][3]
        nowVdw     =masterdatatuple[datlinecount][4]
        nowInter   =masterdatatuple[datlinecount][5]
        newdatstr = '%0.1f,%0.3f,%s,%d,%d,%d\n' % ( nowscore,nowlef,nowlig,nowbatch,nowVdw,nowInter )
        #print "DATA: %s" % newdatstr
        outdatas.write( newdatstr )
        datlinecount = datlinecount+1

    outdatas.close()
