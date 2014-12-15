#!/bin/bash
#PBS -S /bin/bash 
#PBS -l nodes=1:ppn=1
#PBS -l walltime=168:00:00
#PBS -d /gpfs/home/dsantiag/workingDir/
#PBS -o /gpfs/home/dsantiag/workingDir/masterLogFileCAD.log
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
MASTERLOG="$BASEDIR/masterLogFileCAD.log" 

# file containing the list of packages to be processed
### REQUIRED ###
#SEEDFILE="$BASEDIR/packages.index"  
SEEDFILE="$BASEDIR/workingCRAWLAD.lst"


# generated on the fly
# used to keep track of progress
STATUS="$BASEDIR/statusCAD.log"        
touch $STATUS

###### input variables (END)
#####################################

# get the PBS_ARRAYID-nth line in the seed  file
# NOTE: line count starts from 1
PACKAGEDIR=`awk "NR==${PBS_ARRAYID}" $SEEDFILE`
# PACKAGEDIR, despite name, will be a path to the processed Experiment directory; e.g.,

#     /gpfs/group/olson/dsantiag/post_wcg2/AutoDock/procfaah/Exp75

#     /gpfs/group/olson/dsantiag/post_wcg2/Vina/processed/Exp103

#PACKAGENAME=`basename $PACKAGE .tgz` # check this to adapt it to the actual filename scheme...
PACKAGENAME=`basename $PACKAGEDIR`

# PACKAGENAME, despite name, will be something like Exp103 (see PACKAGEDIR)

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
#if [ -s /gpfs/group/olson/dsantiag/post_wcg2/AutoDock/inputs/faah$BATCH.tgz ]; then
  # XXX NOTE: AD processng script processes FAAH AD results directory,
  #  which is a directory containing results tar, md5, seedsave files
  #  (already some degree of compactness) ==> need '-r' option for cp command
  #cp -r $PACKAGEDIR .
  #cp /gpfs/group/olson/dsantiag/post_wcg2/AutoDock/inputs/faah$BATCH.tgz .

if [ -d $PACKAGEDIR ]; then
PYTHON278='/home/rik/pkg/Python-2.7.8/python'
PROCDIRAD='/gpfs/group/olson/dsantiag/post_wcg2/AutoDock/procfaah/'
PROCDIRV='/gpfs/group/olson/dsantiag/post_wcg2/AutoDock/procfaah/'
PROCDIR=$PROCDIRAD
OUTDIR='/gpfs/group/olson/dsantiag/post_wcg2/crawl/' # Universal OUTPUT directory (both AD, V)
CRAWLAD='/home/dsantiag/bin/rik/crawl_AD.py'
CRAWLV='/home/dsantiag/bin/rik/crawl_ADV.py'
NOWSCRIPT=$CRAWLAD
###                       | ###
### your script goes here | ###
###                       v ###

  #/gpfs/home/dsantiag/bin/bash/CFCopt.sh $BATCH

  # maybe add $SCRATCH/work_$PACKAGENAME/
  # as last input to script so that only ONE batch is xferred to
  # $SCRATCH instead of THOUSANDS of processe batches
  $PYTHON278 $NOWSCRIPT $PROCDIR $OUTDIR  --expList "['$PACKAGENAME']" --scratch $SCRATCH/work_$PACKAGENAME/

###                       ^ ###
### your script goes here | ###
###                       | ###

# update status
  echo "$PACKAGENAME completed" >> $STATUS
else
  echo -e "$PACKAGENAME incomplete\n\tUnable to find $PACKAGEDIR" >> $STATUS
fi
