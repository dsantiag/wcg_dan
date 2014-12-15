#!/bin/bash

# TO BE RUN ON THE DIRECTORY CONTAINING THE LIGANDS

# Usage:

# This script is to be called by the perl script, runPMX.pl, which
# gives 7 arguments.  These scripts still need to be optimized as currently,
# a collection of receptors must be singly sequestered in its own directory
# to run these scripts.  This probably entails moving a loop outside of
# another loop, but I will wait until the weekend to do this (11/9-10/2013?)

# Starting batch number
START=$1

# Directory containing targets (single PDBQT)
TARGETS=$2

# Directory contaning ligands (subdirectories "SetOf10k_XXXX")
LIGANDS=$3

#STEP=`ls $TARGETS/*.pdbqt | wc -l`
STEP=1
let TEST=START+STEP-1
echo "START =  $START"
echo "END = $TEST"
echo "STEP = $STEP"
echo "(The next series would start from $TEST)"

PACKAGE_NUMBER=$START
echo $PACKAGE_NUMBER
export PACKAGE_NUMBER
#read X

for i in `ls -d $LIGANDS/package_*`			# FOR AutoDock
#for i in `ls -d $LIGANDS/package_*/fragment_dns`	# FOR AutoDock && FRAGMENTS!!!
	do
		echo -ne " ####\n Processing $i\n ####"

		# REPLACING THIS LINE WITH CODE INSERT BELOW XXX !!!
		#/media/santiagodn/ExtHDelisSeagate/WCG5/LIGANDS/AutoDock/NCIfull/FAAH-PGP_Exp73_A.sh $TARGETS  $i $PACKAGE_NUMBER
		# REPLACING THIS LINE WITH CODE INSERT BELOW XXX !!!

################################################ CODE INSERT vvvvvvvvvvvvvvvvvvvvvvvvvv

################################################ CODE INSERT vvvvvvvvvvvvvvvvvvvvvvvvvv

################################################ CODE INSERT vvvvvvvvvvvvvvvvvvvvvvvvvv

################################################ CODE INSERT vvvvvvvvvvvvvvvvvvvvvvvvvv

################################################ CODE INSERT vvvvvvvvvvvvvvvvvvvvvvvvvv

		# TEMPLATES & VARIABLE DEFINITIONS
		# Input files
		GPFTMPL=$4
		DPFTMPL=$5

		AD4PAR="/export/gridprojects/post_wcg/workspace/WCG5_PARAM/AD4.1_bound.dat"

		# Paths
		MGL_ROOT="/home/dsantiag/local/MGLTools-1.5.7rc1/"
		PYTHON_SH=$MGL_ROOT"bin/pythonsh"
		PREPGPF="/home/dsantiag/bin/python/imported/prepare_gpf4_FAST.py"
		PREPDPF="/home/dsantiag/bin/python/imported/prepare_dpf4_FAST.py"

		# WHERE TGZ FILES ARE MOVED, XXX soon to be $6
		#PACKDIR="/media/santiagodn/ExtHDelisSeagate/WCG5/Packages/outgoing6/"
		PACKDIR=$6

		# WHERE TEMPORARY FILES ARE STORED, XXX soon to be $7
		#TMP="/media/santiagodn/ExtHDelisSeagate/WCG5/tmp6/"
		TMP=$7

		# COMMAND LINE OPTIONS
		REC_DIR=$TARGETS
		LIG_DIR=$i
		PACKTARGET_DIR=$PACKDIR #$3
		echo PACKTARGET DIR $PACKTARGET_DIR

		##########################################################################################################
		##########################################################################################################
		##########################################################################################################
		##########################################################################################################

		# CHECK TEMPLATES
		for CHECK in $GPFTMPL $DPFTMPL $PREPGPF $PREPDPF $AD4PAR
			do
				if [ ! -s $CHECK ]
					then echo -ne " \n     ERROR!\n\n     The following file is not accessible. Check the script variables.\n"
					     echo -ne " \n ==> $CHECK \n\n"
					     echo "* Package creation aborted *"
					     exit 1
				fi
			done

		echo -ne "\n"
		echo "            _______ _______ _________ _______  "
		echo "           |    ___|   _   |   ___   |   |   | "
		echo "           |    ___|       |  |  _   |       | "
		echo "           |___|   |___|___|  |______|___|___| "
		echo "                           |_________| Package Generator "
		echo -ne "\n             date : `date`\n"
		echo -ne "             cwd  : `pwd` \n"
		if [ ! "$REC_DIR" ==  "" -a ! "$LIG_DIR" == ""  -a  ! "$PACKTARGET_DIR" == "" ]
			then
				echo -ne "interactive mode : OFF\n\n"
				INTERACTIVE=0
				echo "Receptor dir: $REC_DIR"
				echo "Ligand dir: $LIG_DIR"
				echo "Pack dir: $PACKTARGET_DIR"
				echo "Start Package number : $START"
			else
				INTERACTIVE=1
				echo -ne "interactive mode : ON\n\n"
				echo "Receptor dir: $REC_DIR"
				echo "Ligand dir: $LIG_DIR"
				echo "Pack dir: $PACKTARGET_DIR"
				echo "Start Package number : $START"
		fi

		# INPUT STAGE
		if [ "$START" == "" ]
			then
				echo -ne " Enter the package starting number > "
				read START
		fi

		#RECEPTORS PATH
		if [ "$REC_DIR" == "" ]
		then
			echo  -ne " Enter the directory of TARGET structures [absolute path]: "
			read REC_DIR
		fi

		while [  `ls $REC_DIR/*.pdbqt &>/dev/null ; echo $?` -gt 0 ]
			do
				echo " # ERROR: Directory selected doesn't contain any PDBQT! #"
				echo  -ne " Enter the directory of TARGET structures [absolute path]: "
				read REC_DIR
			done


		TOT_REC=`ls $REC_DIR/*.pdbqt | wc -l`
		echo -ne "   [ $TOT_REC receptor structures found ] \n\n"

		#LIGANDS PATH
		if [ "$LIG_DIR" == "" ]
		then
			echo -ne " Enter the directory of LIGAND structures [absolute path]: "
			read LIG_DIR
		fi
		while [  `ls $LIG_DIR/*.pdbqt &>/dev/null ; echo $?` -gt 0 ]
			do
				echo " # ERROR: Directory selected doesn't contain any PDBQT! #"
				echo  -ne " Enter the directory of TARGET structures [absolute path]: "
				read LIG_DIR
			done
		TOT_LIG=`ls $LIG_DIR/*.pdbqt | wc -l`
		echo -ne "   [ $TOT_LIG ligand structures found ] \n\n"
		#PACKAGE DIR
		if [ "$PACKTARGET_DIR" == "" ]
			then
				echo -ne " Enter the directory where packages will be created [ default: $PACKDIR ]: "
				read PACKTARGET_DIR
		fi

		if [ "$PACKTARGET_DIR" == "" ]
			then 
				PACKTARGET_DIR=$PACKDIR
		fi
		 

		# CHECK DIRS
		if [ ! -d $PACKDIR ]
			then echo -ne "WARNING: the directory $PACKDIR doesn't exist.\nDo you want to create it? [y,n] "; read ANSWER
			if [ $ANSWER == "y" ] 
				then 
					mkdir -p $PACKDIR
				else
					echo "* Package creation aborted *"
					exit 1
			fi
		fi

		if [ ! -d $TMP ]
			then echo -ne "WARNING: the directory $TMP doesn't exist.\nDo you want to create it? [y,n] "; read ANSWER
			if [ $ANSWER == "y" ] 
				then 
					mkdir -p $TMP
				else
					echo "* Package creation aborted *"
					exit 1
			fi
		fi

		# LOGGING
		let TOTAL_PACKAGES=START+TOT_REC-1
		#LOG="`pwd`/FAAH_PackaGen_"$PACKAGE_NUMBER".log"					#
                LOG=$LIGANDS"/FAAH_PackaGen_"$PACKAGE_NUMBER".log"					#
                touch $LOG
		echo -ne "\n # INFO : $TOT_REC packages are going to be generated [from $START to $TOTAL_PACKAGES ] \n"
		echo -ne " # INFO : The log will be written in the file $LOG\n\n"

		# LOG FILE UPDATE
		echo -ne "Package generation from user `whoami` on `hostname` [`date`]\n" >> $LOG				#
		echo -ne "============================================================================\n\n" >> $LOG	#
		echo -ne "STRUCTURE FILES  \n" >> $LOG
		echo -ne "\tTarget source      :\t$REC_DIR\n" >> $LOG					#  LOG FACILITY
		echo -ne "\tLigand source      :\t$LIG_DIR\n" >> $LOG					#
		echo "----------------------------------------------------" >> $LOG	#
		echo -ne "\n\nPARAMETER FILES  \n" >> $LOG
		echo -ne "\ttemplate GPF       :\t$GPFTMPL\n" >> $LOG
		echo -ne "\ttemplate DPF       :\t$DPFTMPL\n" >> $LOG
		echo -ne "\tPrepareDPF options :\t$DPF_OPT\n\n" >> $LOG
		echo "----------------------------------------------------" >> $LOG	#
		echo "| PCKG |  LIGAND     |    RECEPTOR                 |" >> $LOG				#
		echo "----------------------------------------------------" >> $LOG	#
		#echo " 4792     002059_MC         xMut_md00000.pdbqt"


		# NON-INTERACTIVE INFORMATIONS
		if [ ! "$INTERACTIVE" == "OFF" ]
			then
				echo -ne "Package generation from user `whoami` on `hostname` [`date`]\n"  				#
				echo -ne "============================================================================\n\n"  	#
				echo -ne "STRUCTURE FILES  \n"  
				echo -ne "\tTarget source      :\t$REC_DIR\n"  					#  LOG FACILITY
				echo -ne "\tLigand source      :\t$LIG_DIR\n"  					#
				echo "----------------------------------------------------"  	#
				echo -ne "\n\nPARAMETER FILES  \n"  
				echo -ne "\ttemplate GPF       :\t$GPFTMPL\n"  
				echo -ne "\ttemplate DPF       :\t$DPFTMPL\n"  
				echo -ne "\tPrepareDPF options :\t$DPF_OPT\n\n"  
				echo -ne "\n\t\t [ preparation will start in 5 seconds... ]"
				sleep 5
			else
				#echo -ne "\n\n          IF SOMETHING IS NOT CORRECT\n          THIS WOULD BE A GOOD MOMENT\n         TO STOP THE PROCESS WITH [Ctrl+c]\n\n"
				echo -ne "\n\n           > > > Press ENTER to start < < <\n\n\n"
				read
				echo -ne "\n\n"
		fi

		RECLIST=`ls -1 $REC_DIR/*.pdbqt`
		LIGLIST=`ls -1 $LIG_DIR/*.pdbqt`
		DONE=0

		let PACKAGE=$PACKAGE_NUMBER


		for r in $RECLIST
			do
				RECEPTOR=`basename $r`
				RECNAME=`basename $RECEPTOR .pdbqt`

				#create temporary prep dir for that package
				mkdir $TMP/faah"$PACKAGE"
				pushd $TMP/faah"$PACKAGE" 1>/dev/null

				#make docking dir's and copy proper receptor file and ligand file to them
				for c in $LIGLIST
					do
						LIGAND=`basename $c`
						LIGNAME=`basename $LIGAND .pdbqt`
						echo -ne "\rPackage $PACKAGE :  Preparing ligand $LIGNAME VS $RECNAME target..."
						mkdir faah"$PACKAGE"_"$LIGNAME"_"$RECNAME"
						pushd faah"$PACKAGE"_"$LIGNAME"_"$RECNAME" 1>/dev/null
						#COPY RECEPTOR STRUCTURE
						cp $r .
						#COPY RECEPTOR STRUCTURE
						cp $c .
						# get the parameter file
						cp $AD4PAR .
						# create gpf
						$PYTHON_SH $PREPGPF -l $LIGAND -r $RECEPTOR -i $GPFTMPL -o "$LIGNAME"_"$RECNAME".gpf 1>/dev/null
						# create dpf
						$PYTHON_SH $PREPDPF -l $LIGAND -r $RECEPTOR -i $DPFTMPL -o faah"$PACKAGE"_"$LIGNAME"_"$RECNAME".dpf $DPF_OPT 1>/dev/null
						echo -ne "  $PACKAGE\t  $LIGNAME\t  $RECEPTOR\n" >> $LOG		#	LOGGING
						# popd the docking directory off the stack
						popd 1>/dev/null
					done
				# pop the faahXXXX package directory of the stack
				popd 1>/dev/null
				# tar up the package (remove the untarred original package in the final step)
				echo -ne "\rPackage $PACKAGE :  Creating tgz file...                                                   "
				pushd $TMP 1>/dev/null
				tar -czf $PACKDIR/faah"$PACKAGE".tgz faah"$PACKAGE"
				popd 1>/dev/null
				# create checksum
				echo -ne "\rPackage $PACKAGE :  Calculating MD5 sum...                                                 "
				md5sum $PACKDIR/faah"$PACKAGE".tgz > $PACKDIR/faah"$PACKAGE".md5 
				echo -ne "\rPackage $PACKAGE :  Removing temporary files...                                            "
				\rm -rf $TMP/faah"$PACKAGE"  #  TO BE MODIFIED?  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

				let DONE=DONE+1
				echo -ne "\rPackage $PACKAGE :  done      [ $DONE /$TOT_REC ]        `date`                                        \n"
				echo -ne "\n" >> $LOG
				let PACKAGE=PACKAGE+1
		done

		echo -ne "\n # Package creation finished. # \n"
				echo -ne "\n" >> $LOG
		#cd .. # Yet another guess--this one is for log creation 1 level UP XXX !!!

		#let PACKAGE_NUMBER=$TOTAL_PACKAGES+1 # DELETE GUESS NUMBER 1 (Packages are skipping batchnumbers--too many add+1's???)
                # This seems to be a GOOD guess of NOT skipping batch numbers XXX !!!
		export PACKAGE_NUMBER
		echo "pack number" $PACKAGE_NUMBER

################################################ CODE INSERT ^^^^^^^^^^^^^^^^^^^^^^^^^^

################################################ CODE INSERT ^^^^^^^^^^^^^^^^^^^^^^^^^^

################################################ CODE INSERT ^^^^^^^^^^^^^^^^^^^^^^^^^^

################################################ CODE INSERT ^^^^^^^^^^^^^^^^^^^^^^^^^^

################################################ CODE INSERT ^^^^^^^^^^^^^^^^^^^^^^^^^^







		let PACKAGE_NUMBER=PACKAGE_NUMBER+STEP
	done


		



	 #or i in `ls -d package_00*/`; do echo -ne " ####\n Processing $i\n ####"; FAAH_PackaGenPlus.sh /disk2/work/WCG3/targets/NewStoutXtals_nNewEqMDoutputs  `pwd`/$i $PACKAGE_NUMBER  ; done
