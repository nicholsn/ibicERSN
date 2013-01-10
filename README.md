The IBIC Extract-Remove-Scanner-Noise (ERSN0 Utility.

USAGE:
====================================
Two arguments required
====================================
Program:  ibicERSN -- Version 2.2
Use this routine to:
	Explore-Remove-Scanner-Noise
12/28/12 -- Version 2 -- Improved tissue mask
12/29/12 --         2.1  Fixed Batch Processing Bug & added McFlirt
12/29/12 -- 	  2.2  Reworked non-tissue mask
12/30/12		  2.3  Added PowerSpectrum plot
=================================================================
Usage: 
 ibicERSN <File | List> <tr> 
   Note: Two parameters required -- don't forget the TR

For batch mode -- create a text file listing all NIFTI files to process
   All files in this list must have the same TR
   Use either a relative (e.g. ./ABC/EXY.nii.gz) or a complete path
    specification (e.g. /mnt/home/cjohnson/myexp/mydata/sub1.nii.gz)
   The text file must have a .txt extension
To process a single file simply provide the name of the file.
   using either a relative or complete path specification
