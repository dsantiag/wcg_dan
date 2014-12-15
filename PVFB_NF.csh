#! /bin/csh
# PVFB_NF.csh
#
# PVFB = Prepare Vina FAAH Batch
# NF   = Full NCI Library
#
#					   Daniel N. Santiago, Ph.D.
#                                          12/16/2013 (last modified)
#                                          Unknown First Author of Script
#
# list of target basenames drives the batch creation process
#          for the new VINA FAAH batches
#
# mgl3 - starting batch number
set START = 955100
#
# mgl3 - batch ligands source
set LIGANDS = "/export/gridprojects/wcg/ibm_io/Vina_FAAH/ligands/full_nci_ALL_TAUTOMERS/"
#
# mgl3 - batches targets lists source
#set LISTS = "/home/dsantiag/WCG5_LISTS/"
#set LIST = "Targets_161.lst"
set LISTS = "/export/gridprojects/post_wcg/workspace/WCG5_LISTS/"
set LIST = "Targets_173.lst"
#
# mgl3 - batches output directory
set OUTPUT = "/export/gridprojects/wcg/ibm_io/Vina_FAAH/batches/hold_for_release_mgl3/outgoing5"
#
# mgl3 - library source (which library am I?)
# XXX Note: no slashes! XXX
set LIB = "full_nci_ALL_TAUTOMERS"


# INVOCATION:  just run this script

set p = $START # mod [1]
echo STARTING P IS $p

# *VINA* LIGAND DIR
cd $LIGANDS # mod [2]

foreach t ("`cat $LISTS/$LIST`") # mod [3]
   #foreach d (`cat nf_vina_sets.lst`) # due to batch creation error*
   foreach d (SetOf100k_*)
# While creating scripts for Vina batch creation, many batches were incorrectly
# made AND submitted.  This error involved pointing to Maybridge ligands in the
# Full NCI directory.  A copy of the Maybridge ligands have been placed in the
# NF directory, and this list will ensure that batch creation will be fine.
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
