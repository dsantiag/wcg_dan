#! /bin/bash
# CFCopt.sh

# author:	Daniel N. Santiago, Ph.D., MGL, TSRI, LJ, CA
# created:	2014-04-23
# last
#   modified:	2014-04-24
#
# CFCopt.sh [batch number]
# 
# The first argument should be the batch
# number corresponding to the results directory with format
# 
#   <batch number>_results
#
# and to the input file
#
#   faah<batch number>.tgz
# 
# Input files:
# ============
# 
# It will be assumed that these files as well as the results files are COPIES.  The input file
# is deleted after processing, and the untarred directory will house all of the processed
# files.  This untarred directory
# 
#   faah<batch number>
# 
# will be compressed as <batch number>_procesed.tgz, after processing its files.
# 
# Master LOG.csv file per batch:
# ==============================
#
# A master csv file will be created in the batch directory level with the format
#
#   faah<batch number>.LOG.csv
#
# containing the log info from the raccoon script
# 
# Contents:
# =========
# 
# The files in the processed tar ball of this new script/protocol will have the combined
# contents of the input and processed files EXCEPT for only 1 instance (instead of ~1K) of
# - AD4.1_bound.dat
# - x*.pdbqt
# 
# *.dlg (unless any are bad and cleaned, then also *dlg.bad)
# *.xml (unless any are bad and cleaned, then also *xml.bad)
# *.dpf
# *.gpf
# *.VS.pdbqt (enahnced pdbqt file)
# *.pdbqt (ligand)
# ../AD4.1_bound.dat
# ../x*.pdbqt (receptor pdbqt file)
# ../faah<batch number>.LOG.csv
# ../FAAH_PROC_<batch number>.log
# 
# The receptor pdbqt file and the AD4.1_bound.dat files have all been moved into the
# top-level of the batch directory such that only one file of each exists.  This
# reduces space by eliminating redundant copies, but also allows for multiple receptor
# pdbqt files.

echo "<<<"`date` "BEGIN"

PROCERROR=0
BASE=`pwd`
MYHOME=`echo $HOME`
ERRORLOG="$MYHOME/PROCERROR.log"
LUCKYLOG="$MYHOME/PROCLUCKY.log"
touch $ERRORLOG
touch $LUCKYLOG

ISLOG=0

if [ "$1" == "" ]; then
  PROCERROR=1
else
  BATCH=$1 # immediate
  echo ">>>"
  echo "Working on BATCH $BATCH"
###############################################

k=$(($BATCH/1000))	# use for later when moving to PROCDIR becomes *surgical*

RESDIR="$BASE"/"$BATCH"_results # immediate
INPUTBATCH="$BASE"/faah"$BATCH".tgz
RESTAR="$RESDIR"/faah"$BATCH"_results.tar

# check to see if paths appropriate to server
NOWSERVER=`uname -n`
NOWUSER=`echo $USER`

if [ $NOWUSER == "dsantiag" ]; then
  if [ $NOWSERVER == "mgl3" ] || [ $NOWSERVER == "mgl0" ]; then
    #mgl0?, maybe mgl3?
    MYPYTHONSH="/home/dsantiag/local/MGLTools-1.5.7rc1/bin/pythonsh"
    MYGENVSRESAD="/home/dsantiag/bin/python/AutoDockTools_2013-10-03/Utilities24/generate_vs_results_AD.py"
    MYEXP=$(python /home/dsantiag/bin/python/batchreceptor3.py $BATCH)
    expdir=Exp$MYEXP
    if [ $NOWSERVER == "mgl0" ]; then	# mgl0
      PROCDIR="/export/wcg_permanentARCHIVE/processed2/procfaah/$expdir"
    else				# mgl3
      PROCDIR="/home/dsantiag/post_wcg/AutoDock/procfaah/$expdir"
    fi
  #elif [ $NOWSERVER == "garibaldi00" ]; then
  else
    # garibaldi00
    NOWSERVER="garibaldi00:$NOWSERVER"
    MYPYTHONSH="/gpfs/home/dsantiag/local/MGLTools-1.5.7rc1/bin/pythonsh"
    MYGENVSRESAD="/gpfs/home/dsantiag/bin/python/AutoDockTools_2013-10-03/Utilities24/generate_vs_results_AD.py"
    MYEXP=$(python /gpfs/home/dsantiag/bin/python/batchreceptor3.py $BATCH)
    expdir=Exp$MYEXP
    PROCDIR="/gpfs/group/olson/dsantiag/post_wcg2/AutoDock/procfaah/$expdir"
    #PROCDIR="/gpfs/group/olson/dsantiag/post_wcg2/AutoDock/procfaah/"
  fi

  if [ ! -d $PROCDIR ]; then
    mkdir -p $PROCDIR
  fi

elif [ $NOWUSER == "santiagodn" ]; then

  if [ $NOWSERVER == "elisha" ]; then
    # elisha
    MYPYTHONSH="/santiagodn/local/MGLTools-1.5.7rc1/bin/pythonsh"
    MYGENVSRESAD="/santiagodn/bin/python/AutoDockTools_2013-10-03/Utilities24/generate_vs_results_AD.py"
    MYEXP=$(python /santiagodn/bin/python/batchreceptor3.py $BATCH)
    expdir=Exp$MYEXP
    PROCDIR="/hdd/procfaah/$expdir"
  fi

  if [ ! -d $PROCDIR ]; then
    mkdir -p $PROCDIR
  fi

else

  # get paths from user
  getps=0
  while [ $getps == "0" ]; do
    echo "Specifiy path to pythonsh:"
    read MYPYTHONSH
    if [ -s $MYPYTHONSH ]; then
      getps=1
    fi
  done
  getge=0
  while [ $getps == "0" ]; do
    echo "Specifiy path to Enhanced PDBQT generator script:"
    read MYGENVSRESAD
    if [ -s $MYGENVSRESAD ]; then
      getge=1
    fi
  done
  getpd=0
  while [ $getpd == "0" ]; do
    echo "Specifiy path to processed directory:"
    read PROCDIR
    if [ -d $PROCDIR ]; then
      getpd=1
    fi
  done

fi

# report what's what right now
echo ""
echo " = = = = ="
echo "BATCH: $BATCH"
echo "USER: $NOWUSER"
echo "SERVER: $NOWSERVER"
echo "PYTHONSH: $MYPYTHONSH"
echo "SCRIPT: $MYGENVSRESAD"
echo "PROCESS DIR: $PROCDIR"
echo " = = = = ="
echo "RESULTS DIR: $RESDIR"
echo "INPUT BATCH: $INPUTBATCH"
echo "RESULTS TAR: $RESTAR"
echo " = = = = ="
echo ""

# ===============
# BEGIN CFCopt.sh
# |||||||||||||||
# vvvvvvvvvvvvvvv

if [ -s "$INPUTBATCH" ]; then		# if A  # XXX INPUTS XXX
  if [ -s "$RESTAR" ]; then		# if B  # XXX RESULTS TAR IN DIRECTORY XXX
    # go for it (B)
    echo "<<<"`date` "BEGIN UNTAR RESTAR"
    # untar results tar
    tar xf "$RESTAR" --directory "$RESDIR"/
    echo "<<<" `date`"_END_ UNTAR RESTAR"
    if [ "$?" == "0" ]; then		# if C  # XXX results tar XXX
      # go for it (C)

      RESDIRDONE="$RESDIR"/"$BATCH"_results_done

      # untar input batch
      echo "<<<"`date` "BEGIN UNTAR INPUT TGZ"
      tar xzf "$INPUTBATCH" --directory "$BASE"/
      echo "<<<" `date`"_END_ UNTAR INPUT TGZ"
      WORKDIR="$BASE"/faah"$BATCH"
  
      if [ -d "$WORKDIR" ]; then		# if D  # XXX WORK (INPUT) DIRECTORY XXX
        # go for it (D)

        LOG="$WORKDIR/FAAH_PROC_"$BATCH"_"$NOWSERVER"_"$NOWUSER".log"
        touch $LOG
        ISLOG=1

        echo -e "\n" >> $LOG
        echo      "            _______ _______ _________ _______ _______ ________ _______ _______" >> $LOG
        echo      "   --------|    ___|   _   |   ___   |   |   |       |__    __|    ___|   _   |" >> $LOG
        echo      "    -------|    ___|       |  |  _   |       |__  \__|  |  |  |    ___|      /  " >> $LOG
        echo      "     ------|___|   |___|___|  |______|___|___|  \    |  |__|  |_______|__|\  \  " >> $LOG
        echo      "                           |_________|       |_______|                     \__\ " >> $LOG
        echo      "     MGL, TSRI, LJ, CA " >> $LOG
        echo      "                                                      Enhanced PDBQT Generation " >> $LOG
        echo      "                                                      Version 20140424 \DNS" >> $LOG
        echo -e "\n Date:                `date`\n" >> $LOG
        echo -e "\n Server:              $NOWSERVER\n" >> $LOG
        echo -e   " Working Directory:   `pwd` \n" >> $LOG
        echo -e   " Batch Log:           $LOG \n" >> $LOG
        echo -e   " Python Shell:        $MYPYTHONSH \n" >> $LOG
        echo -e   " Raccoon Script:      $MYGENVSRESAD \n" >> $LOG
        echo -e   " \tVersion 20131003 \SF\n" >> $LOG
        echo -e   " Process Directory:   $PROCDIR \n" >> $LOG
        echo -e   " ERROR Log:           $ERRORLOG \n" >> $LOG
        echo -e "\n     Single-serving processing of FAAH AutoDock batch: $BATCH \n\n" >> $LOG

        echo `date` "BEGIN REPORT (post-untarring main results tgz)" >> $LOG

        echo -e "FAAH Batch $BATCH seems to be a viable processing system" >> $LOG
        echo -e "\tINPUT Batch:\t\t`basename $INPUTBATCH`" >> $LOG
        echo -e "\tRESULTS Directory:\t`basename $RESDIR`" >> $LOG
        echo -e "\tRESULTS Tar File:\t`basename $RESTAR`" >> $LOG
  
        # organize input batch
        #  - move AD4.1_bound.dat, x*qt (receptor file) outside of subdirectories
        cd "$WORKDIR"
        echo "<<<"`date` "BEGIN MOVE DAT/REC/TRACKING/SEED"
        for d in "$WORKDIR"/*_x*; do
          #if [ `cut -d'.' -f1 <<< $d` == "$d" ]; then
          cd $d
          blr=`basename $d`
          lr=Z`cut -d'Z' -f2<<<$blr`
          rec=x`cut -d'x' -f2<<<$lr`.pdbqt
          if [ -s "$d"/AD4.1_bound.dat ]; then	# if D1  # XXX AD4.1_bond.dat XXX
            mv "$d"/AD4.1_bound.dat "$WORKDIR"/
          else					# if D1  # XXX AD4.1_bond.dat XXX (else)
            echo `date` $NOWSERVER "FAAH-_AD_ WARNING: [$BATCH] no AD4.1_bound.dat found in $blr" >> $ERRORLOG
          fi					# if D1  # XXX AD4.1_bond.dat XXX (fi)
          if [ -s "$d"/$rec ]; then			# if D2  # XXX receptor pdbqt XXX
            mv "$d"/$rec "$WORKDIR"/
          else					# if D2  # XXX receptor pdbqt XXX (else)
            echo `date` $NOWSERVER "FAAH-_AD_ WARNING: [$BATCH] no receptor ( $rec ) found in $blr" >> $ERRORLOG
          fi
          cd ..					# if D2  # XXX receptor pdbqt XXX (fi)
          #fi
        done

        # XXX move md5 and seed files to input dir XXX
        if [ -s "$RESDIR"/faah"$BATCH"_results.md5 ]; then	# if D3  # XXX tracking file XXX
          mv "$RESDIR"/faah"$BATCH"_results.md5 "$WORKDIR"/
        else						# if D3  # XXX tracking file XXX (else)
            echo `date` $NOWSERVER "FAAH-_AD_ WARNING: [$BATCH] no tracking file ( faah"$BATCH"_results.md5 ) found in `basename $RESDIR`" >> $ERRORLOG
        fi						# if D3  # XXX tracking file XXX (fi)
        if [ -s "$RESDIR"/faah"$BATCH"_seedsave.tar.gz ]; then	# if D4  # XXX seedsave file XXX
          mv "$RESDIR"/faah"$BATCH"_seedsave.tar.gz "$WORKDIR"/
        else							# if D4  # XXX seedsave file XXX (else)
            echo `date` $NOWSERVER "FAAH-_AD_ WARNING: [$BATCH] no seed file ( faah"$BATCH"_seedsave.tar.gz ) found in `basename $RESDIR`" >> $ERRORLOG
        fi							# if D4  # XXX seedsave file XXX (fi)
        echo "<<<" `date`"_END_ MOVE DAT/REC/TRACKING/SEED"

        # untar up to 1K tar.gz files
        #all files are faah395218_ZINC38830206_1_x4GW6aINleA_00.tar.gz]
        cd $RESDIRDONE
        #for t in `ls $RESDIRDONE/`; do
	#ls $RESDIRDONE/*.tar.gz > datalist
	#ls "$RESDIRDONE"/*.tar.gz > datalist
	#echo "xxxxx" $RESDIRDONE `wc -l datalist`
	#echo "yyyyy" $RESDIRDONE `wc -l datalist2`
	#echo FILETYPE $(file datalist)
	#echo LENGTH $(wc -l datalist)
	#echo $(head datalist)
        #for t in $RESDIRDONE/*.tar; do
        #for t in `<datalist`; do
        echo "<<<"`date` "BEGIN UNTAR SUB_TARGZ"
        for t in "$RESDIRDONE"/*.tar.gz; do
          #if [ `cut -d'.' -f2 <<< $t` == "tar" ]; then

          #echo "))))))" tar xzf $t
          tar xzf $t --directory "$RESDIRDONE"/
          if [ "$?" != "0" ]; then	# if D5  # XXX sub tar.gz XXX
            echo `date` $NOWSERVER "FAAH-_AD_ WARNING: [$BATCH] failed to untar ( `basename $t` ) in `basename $RESDIRDONE`" >> $ERRORLOG
          fi				# if D5  # XXX sub tar.gz XXX (fi)

          #fi
        done
        echo "<<<" `date`"_END_ UNTAR SUB_TARGZ"

        # XXX Single-serving processing XXX
        #for r in `ls $WORKDIR/x*.pdbqt`; do
        #  echo "RECEPTOR: $r" >> $ERRORLOG
        #  $MYPYTHONSH $MYGENVSRESAD -A -d $RESDIRDONE -r $r -l $WORKDIR/faah$BATCH.LOG.csv >/dev/null 2>&1
        #done
        #$MYPYTHONSH $MYGENVSRESAD -A -d $RESDIRDONE/ -r $WORKDIR/$rec -l $WORKDIR/faah$BATCH.LOG.csv >/dev/null 2>&1

        cd "$RESDIRDONE"
        echo "<<<"`date` "BEGIN BATCH PROCESS"
        #echo "COMMAND: $MYPYTHONSH $MYGENVSRESAD  -R -A -d . -r "$WORKDIR"/$rec -l "$WORKDIR"/faah$BATCH.LOG.csv"
        if [ -s "$WORKDIR"/$rec ]; then
          #echo "ls RESDIRDONE dump"
          #ls
	  #echo "DEBUG" $RESDIRDONE
          #/bin/bash
          $MYPYTHONSH $MYGENVSRESAD -A -R -d . -r "$WORKDIR/"$rec -l "$WORKDIR"/faah$BATCH.LOG.csv
        fi
        echo "<<<" `date`"_END_ BATCH PROCESS"

        # XXX Organize per docking job XXX
        echo "<<<"`date` "BEGIN ORGANIZE XML/DLG/VSPDBQT/DLGINFO"
        for d in "$WORKDIR/"*_x*; do
          #echo $d
          blr=`basename $d`
          #lenblr=${#blr}
          if [ `cut -d'.' -f1 <<< $blr` == "$blr" ]; then
          lr=Z`cut -d'Z' -f2 <<< $blr`
          rec=x`cut -d'x' -f2 <<< $lr`.pdbqt
          prolig=`cut -d'x' -f1 <<< $lr`
          lig=${prolig%?}
          #echo "$blr $lr $lig $rec" >> $ERRORLOG

          XCNT=0
          LCNT=0
          ECNT=0
          ICNT=0

          #for e in "$RESDIRDONE"/*_x*; do

          #checke=${e:0:lenblr}
          #if [ "$checke" == "$blr" ]; then
          #echo "$blr $e $checke" 
          # organize (move to process directory)

          #if [ `cut -d'.' -f2 <<< $e` == "xml" ]; then
          #  let "XCNT += 1"
          #  mv $e $WORKDIR/$d/
          #elif [ `cut -d'.' -f2 <<< $e` == "dlg" ]; then
          #  if [ "`cut -d'.' -f3 <<< $e`" == "info" ]; then
          #    let "ICNT += 1"
          #    mv $e $WORKDIR/$d/
          #  else
          #    let "LCNT += 1"
          #    mv $e $WORKDIR/$d/
          #  fi
          #elif [ `cut -d'.' -f2 <<< $e` == "VS" ]; then
          #  let "ECNT += 1"
          #  mv $e $WORKDIR/$d/
          #fi

          for x in "$RESDIRDONE"/$blr*.xml; do
            mv "$x" "$d"/ >/dev/null 2>&1 # takes care of xml
            if [ "$?" == "0" ]; then
              let "XCNT += 1"
            fi
          done

          for l in "$RESDIRDONE"/$blr*.dlg; do
            mv "$l" "$d"/ >/dev/null 2>&1 # takes care of dlg
            if [ "$?" == "0" ]; then
              let "LCNT += 1"
            fi
          done

          for i in "$RESDIRDONE"/$blr*.dlg.info; do
            mv "$i" "$d"/ >/dev/null 2>&1 # takes care of dlg.info
            if [ "$?" == "0" ]; then
              let "ICNT += 1"
            fi
          done

          for e in "$RESDIRDONE"/$lig*VS.pdbqt; do
            mv "$e" "$d"/ >/dev/null 2>&1 # takes care of enhanced pdbqt
            if [ "$?" == "0" ]; then
              let "ECNT += 1"
            fi
          done

          #fi
          #done

          # report to batch processing log file
          echo -e "\t$blr" >> $LOG
          echo -e "\t\tEnhanced PDBQT     FILE COUNT: $ECNT" >> $LOG
          echo -e "\t\tXML                FILE COUNT: $XCNT" >> $LOG
          echo -e "\t\tDLG                FILE COUNT: $LCNT" >> $LOG
          echo -e "\t\tDLG.INFO           FILE COUNT: $ICNT" >> $LOG

          fi
        done
        echo "<<<" `date`"_END_ ORGANIZE XML/DLG/VSPDBQT/DLGINFO"

        # tar and move
        echo "<<<"`date` "BEGIN TAR/MOVE PROCESSED DATA"
        cd "$BASE"
        tar czf "$BATCH"_processed.tgz `basename $WORKDIR`
        PROCTGZ=$BASE/"$BATCH"_processed.tgz
        if [ -s $PROCTGZ ]; then	# if E  # XXX tar processed directory XXX
          mv $PROCTGZ $PROCDIR/
          if [ "$?" != "0" ]; then
            PROCERROR=7
          else
            echo -e "\t\t\t`basename $PROCTGZ` moved to $PROCDIR" >> $LOG
          fi
        else				# if E  # XXX tar processed directory XXX (else)
          PROCERROR=6
        fi				# if E  # XXX tar processed directory XXX (fi)
        echo "<<<" `date`"_END_ TAR/MOVE PROCESSED DATA"

      else				# if D  # XXX WORK (INPUT) DIRECTORY XXX (else)
        PROCERROR=5
      fi				# if D  # XXX WORK (INPUT) DIRECTORY XXX (fi)

    else				# if C  # XXX results tar XXX (else)
      PROCERROR=4
    fi					# if C  # XXX results tar XXX (fi)

  else					# if B  # XXX RESULTS TAR IN DIRECTORY XXX (else)
    PROCERROR=3
  fi					# if B  # XXX RESULTS TAR IN DIRECTORY XXX (fi)

else					# if A  # XXX INPUTS XXX (else)
  PROCERROR=2
fi 					# if A  # XXX INPUTS XXX (fi)

# ^^^^^^^^^^^^^^^
# |||||||||||||||
# *END* CFCopt.sh
# ===============

###############################################

fi

echo "<<<"`date` "BEGIN ERROR REPORT"
# report errors
if [ $PROCERROR -gt 0 ]; then
  # process error
  if [ $PROCERROR -eq 1 ]; then
    # phase 1 error: no batch number given~possible parent script failure
    echo `date` $NOWSERVER "FAAH-_AD_ ERROR [1]: no batch number given~possible parent script failure" >> $ERRORLOG
    if [ $ISLOG -eq 1 ]; then
      echo `date` "FAAH-_AD_ ERROR [1]: no batch number given~possible parent script failure" >> $LOG
    fi
  elif [ $PROCERROR -eq 2 ]; then
    # phase 2 error: no input file
    echo `date` $NOWSERVER "FAAH-_AD_ ERROR [2]: [$BATCH] no input file<`basename $INPUTBATCH`>~possible parent script failure" >> $ERRORLOG
    if [ $ISLOG -eq 1 ]; then
      echo `date` "FAAH-_AD_ ERROR [2]: [$BATCH] no input file<`basename $INPUTBATCH`>~possible parent script failure" >> $LOG
    fi
  elif [ $PROCERROR -eq 3 ]; then
    # phase 3 error: no results directory
    echo `date` $NOWSERVER "FAAH-_AD_ ERROR [3]: [$BATCH] no results tar in directory<`basename $RESDIR`>~possible parent script failure" >> $ERRORLOG
    if [ $ISLOG -eq 1 ]; then
      echo `date` "FAAH-_AD_ ERROR [3]: [$BATCH] no results tar in directory<`basename $RESDIR`>~possible parent script failure" >> $LOG
    fi
  elif [ $PROCERROR -eq 4 ]; then
    # phase 4 error: possible corrupt results tar (main) file
    echo `date` $NOWSERVER "FAAH-_AD_ ERROR [4]: [$BATCH] failed to untar ( `basename $t` ) in `basename $RESDIRDONE`~possible corrupt tar (main) file" >> $ERRORLOG
    if [ $ISLOG -eq 1 ]; then
      echo `date` "FAAH-_AD_ ERROR [4]: [$BATCH] failed to untar ( `basename $t` ) in `basename $RESDIRDONE`~possible corrupt tar (main) file" >> $LOG
    fi
  elif [ $PROCERROR -eq 5 ]; then
    # phase 5 error: no work/input directory
    echo `date` $NOWSERVER "FAAH-_AD_ ERROR [5]: [$BATCH] no input/work directory<`basename $WORKDIR`>~possible corrupted `basename $INPUTBATCH` file" >> $ERRORLOG
    if [ $ISLOG -eq 1 ]; then
      echo `date` "FAAH-_AD_ ERROR [5]: [$BATCH] no input/work directory<`basename $WORKDIR`>~possible corrupted `basename $INPUTBATCH` file" >> $LOG
    fi
  elif [ $PROCERROR -eq 6 ]; then
    # phase 6 error: no work/input directory
    echo `date` $NOWSERVER "FAAH-_AD_ ERROR [6]: [$BATCH] unable to tar working directory <`basename $WORKDIR`>~possible network/server error" >> $ERRORLOG
    if [ $ISLOG -q 1 ]; then
      echo `date` "FAAH-_AD_ ERROR [6]: [$BATCH] unable to tar working directory <`basename $WORKDIR`>~possible network/server error" >> $LOG
    fi
  elif [ $PROCERROR -eq 7 ]; then
    # phase 6 error: no work/input directory
    echo `date` $NOWSERVER "FAAH-_AD_ ERROR [7]: [$BATCH] unable to move processed tgz <`basename $PROCTGZ`> to $PROCDIR~possible network/server error" >> $ERRORLOG
    if [ $ISLOG -eq 1 ]; then
      echo `date` "FAAH-_AD_ ERROR [7]: [$BATCH] unable to move processed tgz <`basename $PROCTGZ`> to $PROCDIR~possible network/server error" >> $LOG
    fi
  fi
else
  # no errors
  echo `date` $NOWSERVER "FAAH-_AD_ LUCKY [0]: [$BATCH] good for crawling" >> $LUCKYLOG
  echo `date` "FAAH-_AD_ LUCKY [0]: [$BATCH] good for crawling" >> $LOG
fi
echo "<<<" `date` "_END_ ERROR REPORT"

if [ $ISLOG -eq 1 ]; then
  echo `date` $NOWSERVER "*END* REPORT FAAH BATCH $BATCH" >> $LOG
fi
echo "<<<" `date` "_END_"
