#! /usr/bin/perl -w
# binVbatches.pl

# usage:

# directory--should be in
# mgl3:~wcg/Vina_FAAH/tracking/DONE/temp_<DATE>/tracking/
# where tracking.lst exists one directory level up
# (probably generated with automated script--maybe?)

# NOTE: \DNS 2014-08-25
# Organization of batches now places batches in
# /export/gridprojects/post_wcg/batches/
# directory in correspsonding ExpN directory

$batch2exp = "/home/dsantiag/bin/python/batchreceptor3.py";
$batchesdir = "/export/gridprojects/post_wcg/batches/";

$log_file = "binVbatches.log";
$touchcommand = "touch $log_file";
system($touchcommand);

open LOGFILE, ">>$log_file" or die "Unable to open $log_file for writing: $!";
$mydate = `date`; chomp($mydate);
print LOGFILE ">>>START: $mydate\n";


$input_file = "../batches.lst";
$klist = ();
$kcnt = 0;

open INPUT, $input_file or die "Unable to open $input_file for reading : $!";
while(<INPUT>){
  $input_line = $_; chomp($input_line);
  $mynum = int(substr($input_line,length($input_line)-11,7));
  #print $mynum."\n";
  #$myknum = init($mynum/1000);
  #print $myknum."\n";
  #if( ! &isInKlist($myknum) ){ &addToKlist($myknum); }

  $expnum = `python $batch2exp $mynum`; chomp($expnum);
  #$expdir = "Exp".$expnum;
  $expdir = $batchesdir."Exp".$expnum;

  if(-d $expdir){
    $command = "mv $input_line $expdir/";
    system($command);
    print LOGFILE "Moved $input_line to $expdir.\n";
  }
  else{
    $command = "mkdir $expdir";
    system($command);
    print LOGFILE "Created $expdir.\n";
    $command = "mv $input_line $expdir/";
    system($command);
    print LOGFILE "Moved $input_line to $expdir.\n";
  }
}
close INPUT;

#print LOGFILE "Total batch directories to be made: $kcnt\n";

#&kListToDirs();
#&kListMoveFiles();

$mydate = `date`; chomp($mydate);
print LOGFILE ">>>*END*: $mydate\n";
close LOGFILE;

# end main
#
# "k" functions below no longer used; results now organized by ExpN,
# where N = experiment number
sub isInKlist{
  $tryK = int($_[0]);
  if($kcnt==0){
    return 0;
  }
  else{
    for($i=0; $i<$kcnt; $i++){
      if($klist[$i]==$tryK){
        return 1;
      }
    }
    return 0;
  }
}

sub addToKlist{
  $putK = int($_[0]);
  $klist[$kcnt]=$putK;
  $kcnt=$kcnt+1;
  print LOGFILE "Added $putK to list.\n";
}

sub kListToDirs{
  for($j=0; $j<$kcnt; $j++){
    $newdir = $klist[$j]."000s";
    $mkdircommand = "mkdir $newdir";
    system($mkdircommand);
    if(-d $newdir){
      print LOGFILE "Succeeded in creating $newdir.\n";
    }
    else{
      print LOGFILE "Failed to create $newdir\n";
    }
  }
}

sub kListMoveFiles{
  for($k=0; $k<$kcnt; $k++){
    $knum = $klist[$k];
    $kdir = $knum."000s";
    if($knum<100){
      $kstr = "00".$knum;
    }
    elsif($knum<1000){
      $kstr = "0".$knum;
    }
    else{
      $kstr = $knum;
    }
    $ksearch = "\*_$kstr\*.txt";
    $movecommand = "mv $ksearch $kdir/";
    system($movecommand);
    print LOGFILE $k.": ".$movecommand."\n";
  }
}

