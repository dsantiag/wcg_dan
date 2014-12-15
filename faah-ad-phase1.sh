#! /bin/bash
# faah-ad-phase1.sh

# possible crontab entry
# @daily /home/dsantiag/bin/bash/faah-ad-phase1.sh >> /var/log/faah-ad_output.log 2>&1

# DEFined scripts and directories:
binAtrackingpl="/home/dsantiag/bin/perl/binAtracking.pl"
binAinputspl="/home/dsantiag/bin/perl/binAinputs.pl"
batch2exp="/home/dsantiag/bin/python/batchreceptor3.py"
Aresultsdir="/export/gridprojects/post_wcg/AutoDock/results/"
Aincomingresdir="/export/gridprojects/wcg/ibm_io/incoming/"

mypwd1=`pwd`

cd /export/gridprojects/wcg/ibm_io/outgoing/

# create temporary directory based on date
nowdate=`date +%Y-%m-%d`
newtempdir=temp_$nowdate
mkdir $newtempdir

masterlog=fa1_proc"$nowdate".log
masterlogdir="/home/dsantiag/log/$masterlog"
touch $masterlogdir

echo ">>>STEP 0: Move tracking to temp directory." >> $masterlogdir

# deal with tracking
for d in *.done_wcg; do
mv $d $newtempdir/
done # for d in *.done_wcg; do

echo ">>>STEP 1: Move tracking to tracking directory" >> $masterlogdir
cd $newtempdir/

ls *.done_wcg > tracking.lst

mkdir tracking
for d in *.done_wcg; do
mv $d tracking/
done # for d in *.done_wcg; do

echo ">>>STEP 2: Create batches (inputs) list from tracking list." >> $masterlogdir
# deal with batches
cp tracking.lst batches.lst
sed -i s/done_wcg/tgz/g batches.lst
mkdir inputs

echo ">>>STEP 3: Move input files to input directory." >> $masterlogdir
for l in $(cat batches.lst); do
mv /export/gridprojects/wcg/ibm_io/outgoing/$l inputs/
done # for l in $(cat batches.lst); do

echo ">>>STEP 4: Create results list from tracking list." >> $masterlogdir
# deal with results
cp tracking.lst results.lst

sed -i s/.done_wcg/_results/g results.lst
sed -i s/faah//g results.lst

echo ">>>STEP 5: Move results directories into results directory." >> $masterlogdir
for l in $(cat results.lst); do
# insertion of organize-into-ExpN-directories
# code inside for-loop
#
batch=`basename $l _results`
expnum=$(python $batch2exp $batch)
expdir=$Aresultsdir"Exp"$expnum
#
# This move will be directly from WCG incoming directory to
# AD results storage directory
if [ -d $expdir ]; then
  mv "$Aincomingresdir""$l" $expdir/
else
  mkdir $expdir
  mv "$Aincomingresdir""$l" $expdir/
fi
#
#mv /export/gridprojects/wcg/ibm_io/incoming/$l .
done # for l in $(cat results.lst); do

echo ">>>STEP 6: Bin (Perl script) and archive tracking files." >> $masterlogdir
# order tracking
cd tracking/

errorpwd=`pwd`
# PERL SCRIPT FOR ORGANIZING
#/home/dsantiag/bin/perl/binAtracking.pl
$binAtrackingpl

cd $errorpwd # just in case modified binAtracking.pl is broken

touch binAtracking.log

cat binAtracking.log >> $masterlogdir
echo "    " >> $masterlogdir
echo "    " >> $masterlogdir
echo "  >>>tracking/inputs  " >> $masterlogdir
echo "    " >> $masterlogdir
echo "    " >> $masterlogdir
cd .. # cd tracking/

echo ">>>STEP 7: Bin (Perl script) and archive input files." >> $masterlogdir
# order batches/inputs
cd inputs/

errorpwd=`pwd`
# PERL SCRIPT FOR ORGANIZING
#/home/dsantiag/bin/perl/binAinputs.pl
$binAinputspl

cd $errorpwd # just in case modified binAinputs.pl is broken \DNS

touch binAinputs.log

cat binAinputs.log >> $masterlogdir
echo "    " >> $masterlogdir
echo "    " >> $masterlogdir
echo "  >>>inputs/processing  " >> $masterlogdir
echo "    " >> $masterlogdir
echo "    " >> $masterlogdir

cd .. # cd inputs/

cd /export/gridprojects/wcg/ibm_io/outgoing/
mv $newtempdir /export/gridprojects/post_wcg/AutoDock/results/

if [ "$?" == "0" ]; then
  echo "Successful move of /export/gridprojects/wcg/ibm_io/outgoing/"$newtempdir" to /export/gridprojects/post_wcg/AutoDock/results/" >> $masterlogdir
else
  echo "UNSUCCESSFUL move of /export/gridprojects/wcg/ibm_io/outgoing/"$newtempdir" to /export/gridprojects/post_wcg/AutoDock/results/" >> $masterlogdir
fi

scp $masterlogdir santiagodn@elisha:/santiagodn/log/

cd $mypwd1
