#! /bin/csh
# PVFB_MB.csh
#
# PVFB = Prepare Vina FAAH Batch
# MB   = Maybridge Library
#
#					   Daniel N. Santiago, Ph.D.
#                                          2014-11-24 (last modified)
#                                          Unknown First Author of Script
#
# list of target basenames drives the batch creation process
#          for the new VINA FAAH batches
#
# MODIFIED: 2014-11-12 for batch generation for OET (Outsmart Ebola Together) Project
# ==>paths changed as well as prefix "FAAH"==>"OET1" 
# mgl3 - starting batch number
set START = $1
#
# mgl3 - batch ligands source
set LIGANDS = "/export/gridprojects/wcg/ibm_io/Vina_FAAH/ligands/nci_div2_pdbqt/"
#
# mgl3 - batches targets lists source
set LISTS = "/home/dsantiag/post_wcg/workspace/WCG5_LISTS/"
#set LIST = "Targets_OET1_Test1.lst"
set LIST = $2
#
# mgl3 - batches output directory
set OUTPUT = "/export/gridprojects/wcg/ibm_io/OET1/batches/hold_for_release_mgl3/outgoing1/"
#
# mgl3 - library source (which library am I?)
# XXX Note: no slashes! XXX
set LIB = "nci_div2_pdbqt"


# INVOCATION:  just run this script

set p = $START # mod [1]
echo STARTING P IS $p

# *VINA* LIGAND DIR
cd $LIGANDS # mod [2]

foreach tpdbqt ("`cat $LISTS/$LIST`") # mod [3]
   set t = "`basename $tpdbqt .pdbqt`"
   foreach d (SetOf100k_*)
      set n = `seq -f%07g $p $p`
#      touch $OUTPUT/OET1_"$t"_"$n".txt # mod [4]
      touch $OUTPUT/OET1_"$n"_"$t".txt # mod [4]
      cd $d
#      echo targets/"$t".pdbqt >> $OUTPUT/OET1_"$t"_"$n".txt # mod [5]
      echo targets/"$t".pdbqt >> $OUTPUT/OET1_"$n"_"$t".txt # mod [5]
      foreach l (*pdbqt)
#         echo ligands/$LIB/"$d"/"$l" >> $OUTPUT/OET1_"$t"_"$n".txt # mod [5]
         echo ligands/$LIB/"$d"/"$l" >> $OUTPUT/OET1_"$n"_"$t".txt # mod [5]
      end
#      echo just finished making OET1_"$t"_"$n".txt
      echo just finished making OET1_"$n"_"$t".txt
      cd ..
      @ p = ($p + 1)
   end
end
