wcg_dan
=======

MGL/TSRI: World Community Grid

WCG Scripts
===========

INFORMATION
===========
README.md
batchreceptor.csv
batchreceptorO.csv

UTILITY
=======
batchreceptor3.py - input: batch number; output: experiment number
generate_vs_results_VINA.py - generates enhanced PDBQT files for AD Vina
                              in FA@H and OET1 projects
generate_vs_results_AD.py - generates enhanced PDBQT files for AutoDock in FA@H project

ORGANIZATION
------------
[mgl3: crontab]
0 0 * * * /home/dsantiag/bin/bash/faah-ad-phase1.sh
		binAtracking.pl (batchreceptor3.py)
		binAinputs.pl (batchreceptor3.py)
		batchreceptor3.py
0 0 * * * /home/dsantiag/bin/bash/faah-vina-phase1.sh
		binVtracking.pl (batchreceptor3.py)
		binVbatches.pl (batchreceptor3.py)
		binVresults.pl (batchreceptor3.py)
0 0 * * * /home/dsantiag/bin/bash/faah-oet1-phase1.sh
		binOtracking.pl (batchreceptor3.py)
		binObatches.pl (batchreceptor3.py)
		binOresults.pl (batchreceptor3.py)

PROCESSING
==========

Enahanced PDBQT file generation
-------------------------------
rc2FAHV.sh
	CFCopt.sh (batchreceptor3.py, generate_vs_results_AD.py)
rc3FAAH.sh
	faah_vina_process_garibaldi00-4.py (generate_vs_results_VINA.py)
		
rc2OET1.sh
	faah_vina_process_garibaldi00-O.py (generate_vs_results_VINA.py)


Crawling
--------
rc4CRAWL.sh - original bash script to test usage on crawl_ADV.py; later
              renamed rc6CRAWLV.sh and modified for AutoDock crawls in
              rc5CRAWLAD.sh

rc5CRAWLAD.sh
	crawl_AD.py

rc6CRAWLV.sh
	crawl_ADV.py

rc6CRAWLO.sh
	crawl_ADO.py
