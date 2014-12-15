#!/bin/bash
#PBS -S /bin/bash 
#PBS -l nodes=1:ppn=1
#PBS -l walltime=24:00:00
#PBS -d /gpfs/home/dsantiag/workingDir/
#PBS -o /gpfs/home/dsantiag/workingDir/masterLogFileV.log
#PBS -j oe 
#PBS -l mem=8gb

# SOURCE: http://intranet.scripps.edu/its/highperformancecomputing/user_guide.html
# Check the values defined above for "PBS -d" and "PBS -o"

#####################################
###### input variables

# this matches the "PBS -d" option for the 
# definition of the working directory
# on the master node
BASEDIR='/gpfs/home/dsantiag/workingDir' 

# local scratch directory on the node. the path will be /scratch/user_name/job_id. 
# the size is limited, range from 48gb to 422gb depending on the node model. 
# the content in this directory will deleted at the end of the job.
SCRATCH="$PBSTMPDIR"


# generated on the fly
# if this matches with the "PBS -o" file above
# both PBS queing and script messages/errors will
# be written in the same file
MASTERLOG="$BASEDIR/masterLogFileV.log" 
#echo ">>>" `date` "START" >> $MASTERLOG
# file containing the list of packages to be processed
### REQUIRED ###
#SEEDFILE="$BASEDIR/packages.index"  
SEEDFILE="$BASEDIR/workingLoad.lst"


# generated on the fly
# used to keep track of progress
STATUS="$BASEDIR/statusV.log"        
touch $STATUS

###### input variables (END)
#####################################

# get the PBS_ARRAYID-nth line in the seed  file
# NOTE: line count starts from 1
PACKAGE=`awk "NR==${PBS_ARRAYID}" $SEEDFILE`
PACKAGENAME=`basename $PACKAGE .tgz` # check this to adapt it to the actual filename scheme...

# copy data locally on the scratch disk on the node
# (check which commands you are going to keep, since 
# tar's will generate their own directories anyway)
cd $SCRATCH
mkdir -p $PACKAGENAME
cd  $PACKAGENAME
#cp $BASEDIR/$PACKAGE .
cp $PACKAGE .

###                       | ###
### your script goes here | ###
###                       v ###

# I coded script to get "everything" from absolute batch path including
# receptor pdbqt file, directory structure to create in processed directory
#/gpfs/home/dsantiag/local/MGLTools-1.5.7rc1/bin/pythonsh /gpfs/home/dsantiag/bin/python/faah_vina_process_garibaldi00_extract.py $PACKAGE
/gpfs/home/dsantiag/local/MGLTools-1.5.7rc1/bin/pythonsh /gpfs/home/dsantiag/bin/python/faah_vina_process_garibaldi00-4.py $PACKAGE

###                       ^ ###
### your script goes here | ###
###                       | ###

# This is already done in script!
# ships data back to where it belongs (assuming your script generated an
# output file called ${PACKAGENAME}_processed.tar.gz
#cd ..
#cp ${PACKAGENAME}_processed.tar.gz $BASEDIR/processed/

#echo ">>>" `date` "_END_" >> $MASTERLOG

# update status
echo "$PACKAGENAME completed" >> $STATUS
