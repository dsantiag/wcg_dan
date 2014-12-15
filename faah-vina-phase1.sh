#! /bin/bash
# faah-vina-phase1.sh

# @daily /home/dsantiag/bin/bash/faah-vina-phase1.sh >> /var/log/faah-vina_output.log 2>&1

mypwd1=`pwd`

cd /export/gridprojects/wcg/ibm_io/Vina_FAAH/tracking/DONE/

# create temporary directory based on date
newtempdir=temp_`date +%Y-%m-%d`
mkdir $newtempdir

masterlogdir=/home/dsantiag/log/
masterlogfile=fv1_proc`date +%Y-%m-%d`.log
masterlog="$masterlogdir""$masterlogfile"
#fv1_proc2014-08-29.log

# deal with tracking
mv *.done_wcg $newtempdir/

cd $newtempdir/

ls *.done_wcg > tracking.lst

# move tracking files into new dir
mkdir tracking
mv *.done_wcg tracking/

# deal with batches
cp tracking.lst batches.lst
sed -i s/done_wcg/txt/g batches.lst
mkdir batches

# look for and get correpsponding batch files
for l in $(cat batches.lst); do
mv /export/gridprojects/wcg/ibm_io/Vina_FAAH/batches/$l batches/ >/dev/null 2>&1
if [ "$?" != "0" ]; then
  mv /export/gridprojects/wcg/ibm_io/Vina_FAAH/batches/DONE/$l batches/ >/dev/null 2>&1
  if [ "$?" != "0" ]; then
    mv /export/gridprojects/wcg/ibm_io/Vina_FAAH/batches/CLAIMED/$l batches/ >/dev/null 2>&1
    if [ "$?" != "0" ]; then
      echo "Unable to find $l"
    else
      echo "Found $l in batches/CLAIMED" >> $masterlog
    fi
  else
    echo "Found $l in batches/DONE" >> $masterlog
  fi
else
  echo "Found $l in batches" >> $masterlog
fi 
done

# deal with results
cp tracking.lst results.lst

sed -i s/.done_wcg/_results.tgz/g results.lst
sed -i s/FAAH_/FAHV_/g results.lst
mkdir results

# get results via list
for l in $(cat results.lst); do
mv /export/gridprojects/wcg/ibm_io/Vina_FAAH/results/$l results/
done

# order tracking
cd tracking/
/home/dsantiag/bin/perl/binVtracking.pl >> $masterlog
echo "    " >> $masterlog
echo "BEGIN binVtracking.log" >> $masterlog
cat binVtracking.log >> $masterlog
echo "_END_ binVtracking.log" >> $masterlog
echo "    " >> $masterlog
#done
cd ..

# order batches
cd batches
/home/dsantiag/bin/perl/binVbatches.pl >> $masterlog
echo "    " >> $masterlog
echo "BEGIN binVbatches.log" >> $masterlog
cat binVbatches.log >> $masterlog
echo "_END_ binVbatches.log" >> $masterlog
echo "    " >> $masterlog
cd ..

# order results
cd results/
/home/dsantiag/bin/perl/binVresults.pl >> $masterlog
echo "    " >> $masterlog
echo "BEGIN binVresults.log" >> $masterlog
cat binVresults.log >> $masterlog
echo "_END_ binVresults.log" >> $masterlog
echo "    " >> $masterlog
cd ..

# copy masterlog to elisha
scp $masterlog santiagodn@elisha:/santiagodn/log/

# move working dir to Vina results dir
mv /export/gridprojects/wcg/ibm_io/Vina_FAAH/tracking/DONE/$newtempdir /export/gridprojects/post_wcg/Vina/results/
if [ "$?" == "0" ]; then
  echo "Moved $newtempdir to /export/gridprojects/post_wcg/Vina/results/" >> $masterlog
fi

cd $mypwd1
