#! /usr/bin/env perl
# author:	Daniel N. Santiago, Stefano Forli

# created:	April 10, 2014
# last
# modified:	April 16, 2014

# modifications notes: This is the 4th version of this script
#               where the 3rd version is running off files
#               in dsantiag home directory (/gpfs/home/dsantiag/)
#               The 4th version will run from a larger space
#               on garibaldi00 (/gpfs/group/olson/dsantiag/)

# modification specifications:

#               Differences:
#               This version is called by

#                    /gpfs/group/olson/dsantiag/workingDir/rc2FAHV.sh

#               and will track 

# usage: ~/bin/python/faah_vina_process.py /path/to/<faah_vina_results_tgz>
# usage: CALLED BY GARIBALDI00 submission script

# purpose:	This is a conversion of a python script for use on garibaldi00
#               to aid in mass batch processing of incoming Vina results files
#               from World Community Grid (WCG). [faah_vina_processing.py,
#               2013/10/04 /DNS]
#
#               The original file was created for use on mgl0 then mgl3
#               to process batches IF an experiment was completed, meaning
#               that all batches for a given library and set of receptors
#               had all been received from WCG.
#
#               With incoming through-put, this "waitibng for completion"
#               was inefficient in terms of disk space and turnaround time
#               for analysis and proposals for compound testing.  In March
#               2014, the DAILY processing of incoming results files was
#               automated on mgl3.  This leaves a large amount of docking
#               results to be processed, approximately a year's worth
#               of data.
#
#               The code for singular batch file processing has been
#               extracted from faah_vina_processing.py and will be combined
#               with Stefano Forli's submission script, which allows for
#               job array batch submission on server garibaldi00.scripps.edu.

# use of this script entails modification of the following paths:
# _+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_
pythonsh157 = "/gpfs/home/dsantiag/local/MGLTools-1.5.7rc1/bin/pythonsh"
genvinares = "/gpfs/home/dsantiag/local/MGLTools-1.5.7rc1/MGLToolsPckgs/AutoDockTools/Utilities24/generate_vs_results_VINA.py"
targetdir = "/gpfs/home/dsantiag/post_wcg/Vina/targets/"
procdir = "/gpfs/group/olson/dsantiag/post_wcg2/Vina/processed/"
# _+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+
# use of this script entails modification of the above paths_+_^

# import START

import sys
import os
from os import listdir
from os.path import isfile, join
import tarfile
import string
import subprocess
import shutil
import time
# import *END*

nowtime = time.asctime( time.localtime(time.time()) )
print "<<<%s BEGIN" % nowtime

# other variables START

TRUE = 1
DEBUG = 0

# other variables *END*

# submission script will read this list file and pass each line as argument to THIS script

# Note: target receptor pdbqt file name can be gotten from sys.argv[1]

# So, sys.argv[1] will be `basename $1`, e.g., FAHV_x3NF8_A_IN_LEDGF_0050058_results.tgz

if len( sys.argv )>1:
    #/gpfs/home/dsantiag/post_wcg/Vina/results/Exp48/Results_x3NF8_A_IN_LEDGF/FAHV_x3NF8_A_IN_LEDGF_0050058_results.tgz
    respath=sys.argv[1]

    #FAHV_x3NF8_A_IN_LEDGF_0050058_results.tgz
    r=os.path.split(respath)[1]				# defined r

    #/gpfs/home/dsantiag/post_wcg/Vina/results/Exp48/Results_x3NF8_A_IN_LEDGF
    resdir=os.path.split(respath)[0]

    #x3NF8_A_IN_LEDGF.pdbqt
    targetpdbqt=targetdir+resdir.split('Results_')[1]+'.pdbqt'	# defined targetpdbqt

    #/gpfs/home/dsantiag/post_wcg/Vina/results/Exp48
    expdir=os.path.split(resdir)[0]

    expprocdir=procdir+os.path.split(expdir)[1]+'/'+os.path.split(resdir)[1]+'/'

    if os.path.exists(expprocdir):
        print "Path (%s) exists!\n" % expprocdir
    else:
        command = "mkdir -p %s" % expprocdir
        subprocess.call(command, shell=TRUE)

else:
    sys.exit('No faah tgz file path specified.')

# -=-=-=-=-=--=-=-=-=-=-
# BEGIN BATCH PROCESSING
subprocess.call("echo \"GARIBALDI00 FAAH VINA PROCESSING [START]:\"`date`", shell=TRUE) # REPORT!
subprocess.call("echo \"    PROCESSING %s\"" % r, shell=TRUE) # REPORT!

nowtime = time.asctime( time.localtime(time.time()) )
print "<<<%s BEGIN UNTAR TARGZ" % nowtime

vinatar = tarfile.open(r)
vinatar.extractall()
vinatar.close()

nowtime = time.asctime( time.localtime(time.time()) )
print "<<<%s _END_ UNTAR TGZ" % nowtime

vinatardir = r.rsplit(".tgz")
currenttardir = vinatardir[0]

trash=os.getcwd()+'/trash'
command = "mkdir %s" % trash
subprocess.call(command, shell=TRUE)

os.chdir(currenttardir)

AllLigs_log = "AllLigs_" + currenttardir + ".LOG.csv"
command = "touch %s" % AllLigs_log
subprocess.call(command, shell=TRUE)

nowtime = time.asctime( time.localtime(time.time()) )
print "<<<%s BEGIN UNTAR SUB_TARS" % nowtime

tarfiles = [ t for t in listdir(os.getcwd()) if isfile(join(os.getcwd(),t))]
for t in tarfiles:
    if(t.find('.tar')>0):
        vinatar2 = tarfile.open(t)
        vinatar2.extractall()
        vinatar2.close()

        vinatardir2 = t.rsplit(".tar")
        currenttardir2 = vinatardir2[0]
        subprocess.call("echo \"        PROCESSING %s\"" % currenttardir2, shell=TRUE) # REPORT!
        os.chdir(currenttardir2)

        subprocess.call("mv *log.txt *pdbqt ..", shell=TRUE)

        os.chdir("..") # leaving tar
        #move tar file and the directory to 'trash'
        command = "mv %s %s %s" % (t, currenttardir2,trash)
        subprocess.call(command, shell=TRUE)

nowtime = time.asctime( time.localtime(time.time()) )
print "<<<%s _END_ UNTAR SUB_TARS" % nowtime


nowtime = time.asctime( time.localtime(time.time()) )
print "<<<%s BEGIN PROCESS" % nowtime

# this whole script is for this ONE command (speed-up=2X for a total of ~27X)
command = "%s %s -d . -r %s -m 1 -x 0.04 -l %s" % (pythonsh157,genvinares,targetpdbqt,AllLigs_log)
subprocess.call(command, shell=TRUE)

nowtime = time.asctime( time.localtime(time.time()) )
print "<<<%s _END_ PROCESS" % nowtime

nowtime = time.asctime( time.localtime(time.time()) )
print "<<<%s BEGIN ORGANIZE OUT/REC" % nowtime
# delete all pre-processed pdbqt files
command = "mv *out.pdbqt %s" % trash
subprocess.call(command, shell=TRUE)

# copy target receptor pdbqt into directory
command = "cp %s ." % targetpdbqt
subprocess.call(command, shell=TRUE)

nowtime = time.asctime( time.localtime(time.time()) )
print "<<<%s _END ORGANIZE OUT/REC" % nowtime

os.chdir("..") # return to tar main

nowtime = time.asctime( time.localtime(time.time()) )
print "<<<%s BEGIN RENAME/TAR/MOVE PROCESS BATCH" % nowtime

#change directory name from "*_results" to "*_processed"
source = currenttardir
destination = currenttardir.rsplit("results")[0]+"processed"
if(DEBUG):
    print "Renaming processed directory: %s\t%s" % (source, destination)
shutil.move(source, destination)

# tarring processed file
proctgz = destination + ".tgz"
if(DEBUG):
    print "Tarring processed dir: %s\t%s" % (proctgz, destination)
vinatar3 = tarfile.open(proctgz, "w:gz")
for name in [destination]:
    vinatar3.add(name)
vinatar3.close()

# moving processed tgs to processed dir
source = proctgz
destination = expprocdir
if(DEBUG):
    print "Moving processed tgz to processed dir: %s\t%s" % (source, destination)
shutil.move(source, destination)
subprocess.call("echo \"GARIBALDI00 FAAH VINA PROCESSING [[END]]:\"`date`", shell=TRUE) # REPORT!

nowtime = time.asctime( time.localtime(time.time()) )
print "<<<%s _END_ RENAME/TAR/MOVE PROCESS BATCH" % nowtime

# *END* BATCH PROCESSING
# -=-=-=-=-=--=-=-=-=-=-
nowtime = time.asctime( time.localtime(time.time()) )
print "<<<%s _END_" % nowtime
