#! /bin/csh
# PVFB_OT.csh
#
# PVFB = Prepare Vina FAAH Batch
# OT   = Otava Library
#
#					   Daniel N. Santiago, Ph.D.
#                                          12/16/2013 (last modified)
#                                          Unknown First Author of Script
#
# list of target basenames drives the batch creation process
#          for the new VINA FAAH batches
#
# mgl3 - starting batch number
set START = 12345
#
# mgl3 - batch ligands source
set LIGANDS = "/export/gridprojects/wcg/ibm_io/Vina_FAAH/ligands/otava_Sep2009/"
#
# mgl3 - batches targets lists source
set LISTS = "/home/dsantiag/WCG5_LISTS/"
set LIST = "testVina.lst"
#
# mgl3 - batches output directory
set OUTPUT = "/export/gridprojects/wcg/ibm_io/Vina_FAAH/batches/hold_for_release_mgl3/outgoingOT"
#
# mgl3 - library source (which library am I?)
# XXX Note: no slashes! XXX
set LIB = "otava_Sep2009"


# INVOCATION:  just run this script

set p = $START # mod [1]
echo STARTING P IS $p

# *VINA* LIGAND DIR
cd $LIGANDS # mod [2]

foreach t ("`cat $LISTS/$LIST`") # mod [3]
   foreach d (SetOf10k_*)
      set n = `seq -f%07g $p $p`
      touch $OUTPUT/FAAH_"$t"_"$n".txt # mod [4]
      cd $d
      echo targets/"$t".pdbqt >> $OUTPUT/FAAH_"$t"_"$n".txt # mod [5]
      foreach l (*pdbqt)
         echo ligands/$LIB/"$d"/"$l" >> $OUTPUT/FAAH_"$t"_"$n".txt # mod [5]
      end
      echo just finished making FAAH_"$t"_"$n".txt
      cd ..
      @ p = ($p + 1)
   end
end
