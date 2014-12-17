#! /usr/bin/env python
# faah-analyze-crawl-summ.py

# TO BE RUN ON MGL0 (so far)

import glob, sys, os, math

datFile = '/home/dsantiag/dat/vina539.dat'
batchRecept = '/home/dsantiag/batchreceptor.csv'

# crawl available on mgl0:

# 115-120
# 91-96

# The following directory contains csv files that contain
# the crawl "summ" data PER RECEPTOR
# These files were generated from
# python /home/dsantiag/bin/python/batchreceptor5.py 115
# (example is for Exp115)
# Example output:

#mgl0:/export/wcg/crawl/data/Exp115 % ll
#total 223140
#-rw-r--r-- 1 dsantiag olson  9158335 Nov 20 14:47 115_x1ZTZ_prASw0c0.csv
#-rw-r--r-- 1 dsantiag olson 10438516 Nov 20 14:48 115_x3I8WAprASw0c0.csv
#-rw-r--r-- 1 dsantiag olson 10448019 Nov 20 14:48 115_x3KF0_prASw0c0.csv
#...

crawlDatDir  = '/export/wcg/crawl/data' # mgl0
crawlNormDir = '/export/wcg/crawl/norm' # mgl0
try:
    expNum = sys.argv[1]
except:
    print "\nERROR:----------\\\n"
    print 'Please enter an experiment number when using this script.'
    print 'Exiting ...'
    print "\nERROR:----------/\n"
    sys.exit()

crawlNormDir = '/export/wcg/crawl/norm/Exp' + expNum # mgl0

if not os.path.isdir( crawlNormDir ):
    os.makedirs( crawlNormDir )

try:
    zCut = float( sys.argv[2] )
except:
    print "\nERROR:----------\\\n"
    print 'Please enter a normalized cutoff value after the experiment number.'
    print 'Recommended value should be less than -3.0'
    print 'Exiting ...'
    print "\nERROR:----------/\n"
    sys.exit()

expDir = crawlDatDir + '/Exp' + expNum
sumList  = glob.glob(expDir +'/*.csv')

try:
    logNow = open( crawlNormDir + '/Exp'+expNum+'.log', 'a')

except:
    print 'Unable to write to',crawlNormDir + '/Exp'+expNum+'.log'
    print 'Exiting ...'
    sys.exit()

if len( sumList ) == 0:
    print "\nERROR----------\\\n"
    print 'Are you sure that you ran batchreceptor5.py script?'
    print 'Check the existance of this directory:',expDir
    print 'Exiting ...'
    print "\nERROR:----------/\n"
    sys.exit()

for i,recData in enumerate( sumList ):
    # '/export/wcg/crawl/data/Exp115/115_x3KFP_prASw0c0.csv'
    recRoot = os.path.split( recData )[1].lstrip( str(expNum) + '_' ).rstrip( '.csv' )
    #print recRoot

    zCutoff = zCut

    try:
        tst = open(crawlNormDir+'/'+'tst.csv','w')
        os.remove( crawlNormDir+'/'+'tst.csv'  )
    except:
        print 'faah-analyze-crawl-summ.py: creating crawlNormDir directory',crawlNormDir
        os.makedirs( crawlNormDir )

    # get statistics from datFile using recRoot
    # EXAMPLE: grep x3KF0_prASw1c0 ~/dat/vina539.dat

    for line in open( datFile ):
        if recRoot in line:
            refStats = line
    if not refStats:
        print "\nERROR----------\\\n"
        print 'Unable to find statistics on',recRoot
        print 'Exiting ...'
        print "\nERROR:----------/\n"
        sys.exit()
    #else:
    #    print refStats

    # x3KFP_prASw0c0,1880,-7.38856382978723,1.31178509563342,-0.573440807319853,-2.42671172381925,-0.384668617021276,0.0366783732053038,0.000448315073342883,-2.99955180417525,39.4457446808511,7.5562652314686,19.0273189392401,16.0222578089619,2.35212765957447,2.64857684285664,2.33769778789717,-0.662924022936543,140,762615

# 0,recRoot
# 1,N
# 2,mnScore
# 3,sdScore
# 4,skScore
# 5,krScore
# 6,mnLEF
# 7,sdLEF
# 8,skLEF
# 9,krLEF
#10,mnNvdw
#11,sdMvdw
#12,skNvdw
#13,krNvdw
#14,mnNinter
#15,sdNinter
#16,skNinter
#17,krNinter
#18,expnum
#19,batch always 140

    getStats = refStats.split( ',' )
    totalN   = int( getStats[1] )
    mnScore  = float( getStats[2] )
    sdScore  = float( getStats[3] )
    mnLEF    = float( getStats[6] )
    sdLEF    = float( getStats[7] )
    mnNvdw   = float( getStats[10] )
    sdNvdw   = float( getStats[11] )
    mnNinter = float( getStats[14] )
    sdNinter = float( getStats[15] )

    #mgl0:/export/wcg/crawl/data/Exp115 % head 115_x1ZTZ_prASw0c0.csv
    #-11.4,-0.285,ZINC05707314,396788,30,0

    if len(sys.argv) > 3:
        maxNz = int( sys.argv[3] )
        e = open( recData, 'r' )
        for i in range(0,maxNz):
           e.readline()
        getCheck = e.readline()
        getScore = float( getCheck.split( ',' )[0] )
        #print 'zCutoff',zCutoff
        #print 'getScore [%d] %f' % (maxNz,getScore)
        #print 'mnScore',mnScore
        #print 'sdScore',sdScore
        logInfo = "( %f - %f )/ %f\n" % (getScore, mnScore, sdScore)
        logNow.write( logInfo )
        getZ = (getScore - mnScore)/sdScore
        logInfo = "getZ [%d] %f\n" % (maxNz,getZ)
        logNow.write( logInfo )
        zCutoff = getZ - 0.1
    else:
        maxNz = 0

    gList = []

    hitCount = 0
    f = open( recData, 'r')
    for line in f:
        getData = line.split( ',' )
        nowScore = float( getData[0] ) 
        nowLEF   = float( getData[1] )
        nowLig   = getData[2]
        nowBatch = getData[3]
        nowNvdw   = int( getData[4] )
        nowNinter = int( getData[5] )

        zScore   = (nowScore - mnScore)/sdScore
        zLEF     = (nowLEF - mnLEF)/sdLEF
        zNvdw     = (nowNvdw - mnNvdw)/sdNvdw
        zNinter   = (nowNinter - mnNinter)/sdNinter

        if zScore <= zCutoff:
            goldLine = "%s,%s,%s,%0.4f,%0.4f,%0.4f,%0.4f,%0.4f,%0.4f,%0.4f,%0.4f\n" % (nowLig,recRoot,nowBatch,zScore,nowScore,zLEF,nowLEF,zNvdw,nowNvdw,zNinter,nowNinter)
            gList.append( goldLine )
            hitCount = hitCount+1

    logInfo = "%s,%d,%f,%d\n" % (recRoot,hitCount,zCutoff,maxNz)
    logNow.write(logInfo)
    #recNormDat = expNum + "_" + recRoot + "_" + str( zCutoff ) + '_' +str( maxNz  ) + ".csv"
    recNormDat = '%s_%s_%0.4f_%d_%d.csv' % (str(expNum), recRoot, zCutoff, maxNz, hitCount)
    #print 'Attempting to open', recNormDat

    try:
        g = open( crawlNormDir + '/' + recNormDat, 'w' )
    except:
        print "\nERROR----------\\\n"
        print 'Unable open file in',crawlNormDir
        print 'Exiting ...'
        print "\nERROR:----------/\n"
        sys.exit()

    for line in gList:
        g.write( line )

    g.close()

logNow.close()
