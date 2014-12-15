#!/bin/bash
#PBS -S /bin/bash 
#PBS -l nodes=1:ppn=1
#PBS -l walltime=02:00:00
#PBS -d /gpfs/home/dsantiag/workingDir/
#PBS -o /gpfs/home/dsantiag/workingDir/masterLogFileA.log
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
MASTERLOG="$BASEDIR/masterLogFileA.log" 

# file containing the list of packages to be processed
### REQUIRED ###
#SEEDFILE="$BASEDIR/packages.index"  
SEEDFILE="$BASEDIR/workingFAAH.lst"


# generated on the fly
# used to keep track of progress
STATUS="$BASEDIR/statusA.log"        
touch $STATUS

###### input variables (END)
#####################################

# get the PBS_ARRAYID-nth line in the seed  file
# NOTE: line count starts from 1
PACKAGEDIR=`awk "NR==${PBS_ARRAYID}" $SEEDFILE`
#PACKAGENAME=`basename $PACKAGE .tgz` # check this to adapt it to the actual filename scheme...
PACKAGENAME=`basename $PACKAGEDIR`

# example of esults directory: 102873_results
BATCH=`cut -d'_' -f1 <<< $PACKAGENAME`

# copy data locally on the scratch disk on the node
# (check which commands you are going to keep, since 
# tar's will generate their own directories anyway)
cd $SCRATCH
mkdir -p work_$PACKAGENAME
cd  work_$PACKAGENAME
#cp $BASEDIR/$PACKAGE .
#cp $PACKAGEDIR .

# check to make sure input file exists
if [ -s /gpfs/group/olson/dsantiag/post_wcg2/AutoDock/inputs/faah$BATCH.tgz ]; then
  # XXX NOTE: AD processng script processes FAAH AD results directory,
  #  which is a directory containing results tar, md5, seedsave files
  #  (already some degree of compactness) ==> need '-r' option for cp command
  cp -r $PACKAGEDIR .
  cp /gpfs/group/olson/dsantiag/post_wcg2/AutoDock/inputs/faah$BATCH.tgz .

###                       | ###
### your script goes here | ###
###                       v ###

  /gpfs/home/dsantiag/bin/bash/CFCopt.sh $BATCH

###                       ^ ###
### your script goes here | ###
###                       | ###

# update status
  echo "$PACKAGENAME completed" >> $STATUS
else
  echo -e "$PACKAGENAME incomplete\n\tUnable to find faah$BATCH.tgz" >> $STATUS
fi
