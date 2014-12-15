#! /usr/bin/perl -w
# runPMX.pl

# rough outline:  used together with PMX.sh, this should take all receptors, which
# have been placed singly in their own directories, and generate packages for one
# particular library.  From the standpoint of the FAAH status page, any one column
# of a table of experiments (i.e., 1 experiment).

# This perl script will take in the FIRST batchnumber of an experiment, as well as
# a second value to define the library used.  From this, the PMX.sh script will be
# called with the 7 arguments (see lines 79-80) in order to create all the batches
# for each receptor.

# Using the knowledge of number of packages in a given library, the PMX.sh is
# called again with an offset from the previous starting batch number, etc.

# Note: PMX.sh is a combined script from 2 other scripts, which were not optimzed
# for multiple receptor batch generations.  When given a collection of rceptors,
# the batch numbers were dicontiguous in regards to receptors making analysis
# a logistics nightmare.

# XXX !!! Edit the LIST on LINE 37 !!! XXX

#/mnt/raid/WCG5/LIGANDS/AutoDock/ChemBridge

use Switch;

$start = $ARGV[0];

$libval = $ARGV[1];

$rec_list = $ARGV[2];

$PMX = "/home/dsantiag/bin/bash/PMX.sh";

$lib_dir = "/export/gridprojects/post_wcg/workspace/WCG5_LIGANDS/AutoDock/";
$tmpl_dir = "/export/gridprojects/post_wcg/workspace/WCG5_GPF_DPF/";
$rec_dir = "/export/gridprojects/post_wcg/workspace/WCG5_TARGETS/";
$list_dir = "/export/gridprojects/post_wcg/workspace/WCG5_LISTS/";
$hold_dir = "/export/gridprojects/wcg/ibm_io/outgoing/hold_for_release_mgl3/";
$tmp_dir= "/export/gridprojects/post_wcg/workspace/WCG5_tmp/";

$list_file = $list_dir.$rec_list;  # This can be ANYWHERE!

switch($libval){
  case 1 {
        $ligcode="nf";
	$offset = 317;
  }
  case 2 {
        $ligcode="en";
	$offset = 2345;
  }
  case 3 {
        $ligcode="cb";
	$offset = 1014;
  }
  case 4 {
        $ligcode="as";
	$offset = 507;
  }
  case 5 {
        $ligcode="vm";
	$offset = 1504;
  }
  case 6 {
        $ligcode="mb";
	$offset = 77;
  }
  else   {
    die "\nNo library defined.\n\t1=NF,2=EN,3=CB,4=AS,5=VM,6=MB\n$!\n";
  }
}
    $lig_dir = $lib_dir.$ligcode."/";
    $packdir = $hold_dir.$ligcode."/";
    $tempdir = $tmp_dir.$ligcode."/";
    #$skipdir = $$list_dir.$ligcode."ADskip.lst";


$bnum = $start;
open LIST, $list_file or die "Failed to open $list_file for reading: $!";
while(<LIST>){ 
  $rec_name = $_; chomp($rec_name);
  $rec_root = substr($rec_name,0,length($rec_name)-6);
  $rec_file_dir = $rec_dir.$rec_root."/";

  $gpftmpl = $tmpl_dir.$rec_root.".gpf";
  $dpftmpl = $tmpl_dir.$rec_root.".dpf";
  #              BASH:   $1      $2           $3        $4      $5        $6      $7
  #$command = "./PMX.sh $bnum $rec_file_dir $lig_dir $gpftmpl $dpftmpl $packdir $tempdir";
  $command = "$PMX $bnum $rec_file_dir $lig_dir $gpftmpl $dpftmpl $packdir $tempdir";
  system($command);

  $bnum = $bnum+$offset;
}
#continue{
#  $bnum = $bnum+$offset;
#}
close LIST;

# end main
# begin subs

#sub checkSkip{
#    $checkNum=$_; chomp($checkNum);
#    open CHKSKP, $skipdir or die "Unable to open $checkFile for reading: $!";
#    while(<CKHSKP>){
#       $input_line=$_; chomp($input_line);
#       if( index('-',$input_line) == -1 ){ # if NOT range
#           if( int($input_line) == int($checkNum) }{
#               return 1;
#           }
#       }
#       else{ # else IS range
#           @getrange=split('-',$input_line);
#           $minrange=$getrange[0];
#           $maxrange=$getrange[1];
#           if( int($checkNum) >= int($minrange) ){
#               if( int($checkNum) <= int($maxrange) ){
#                   return 1;
#               }
#           }
#       } 
#    }
#    close CHKSKP;
#    return 0;
#}
