The IBIC Extract-Remove-Scanner-Noise (ERSN) Utility.
=====================================================

Usage:
------
`ibicERSN <File | List> <tr>`
   
Note: Two parameters required -- don't forget the TR

For batch mode -- create a text file listing all NIFTI files to process
   - All files in this list must have the same TR
   - Use either a relative (e.g. ./ABC/EXY.nii.gz) or a complete path 
     specification (e.g. /mnt/home/cjohnson/myexp/mydata/sub1.nii.gz)
   - The text file must have a .txt extension

To process a single file simply provide the name of the file.
   - using either a relative or complete path specification
