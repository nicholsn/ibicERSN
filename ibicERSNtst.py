"""
IBIC Extract Remove Scanner Noise
"""
__author__ = 'Nolan Nichols <nolan.nichols@gmail.com>'

import nipype.interfaces.fsl as fsl
import nipype.interfaces.fsl.maths as maths
import nipype.pipeline.engine as pe         # the workflow and node wrappers

in_fmri = "/Users/nolan/Downloads/_20_Resting.nii"
TR = 2.0

# Execute Motion Correction
# mcflirt -in ${AFILE}
mcflirter = pe.Node(interface=fsl.MCFLIRT(), name="mcflirt")

# Generate a tissue mask
# fslmaths ${AFILE}_mcf ${UNIQUEID}_prefiltered_func_data -odt float
floater = pe.Node(interface=maths.ChangeDataType(), name="mcf2float")
floater._suffix = "_prefiltered_func_data"
floater.inputs.output_datatype = "float"

# fslmaths ${UNIQUEID}_prefiltered_func_data -Tmax ${UNIQUEID}_max_func
tmaxer = pe.Node(interface=maths.MaxImage(), name="Tmax")
tmaxer._suffix = "_max_func"
tmaxer.dimension = "T"

# bet ${AFILE}_mcf.nii.gz ${UNIQUEID}_brain.nii.gz
better = pe.Node(interface=fsl.BET(), name="bet")
better._suffix = '_brain' 

# fslmaths ${UNIQUEID}_brain.nii.gz -bin -kernel gauss 12 -ero -ero ${UNIQUEID}_brain_e2.nii.gz
eroder = pe.Node(interface=maths.MultiImageMaths(), name="erode")
eroder.inputs.op_string = "-bin -kernel gauss 12 -ero -ero"
eroder._suffix = "_ero2"

# fslmaths ${UNIQUEID}_brain_e2.nii.gz -kernel gauss 12 -dilM -dilM -dilM ${UNIQUEID}_brain_e2d3.nii.gz
dilator = pe.Node(interface=maths.MultiImageMaths(), name="dilate")
dilator.inputs.op_string = "-kernel gauss 12 -dilM -dilM -dilM"
dilator._suffix = "_dil3"

# fslsplit ${UNIQUEID}_brain_e2d3.nii.gz temp_slice -z
splitter = pe.Node(interface=fsl.Split(), name="split")
splitter.inputs.dimension = "z"
splitter.inputs.out_base_name = "temp_slice"

# fslmaths ${UNIQUEID}_brain_e2d3.nii.gz -Zmax temp_base.nii.gz
zmaxer = pe.Node(interface=maths.MaxImage(), name="Zmax")
zmaxer.dimension = "Z"

# fslmerge -z ${UNIQUEID}_max_brain.nii.gz ${mergelist}
merger = pe.Node(interface=fsl.Merge(), name="Merge")
merger.inputs.dimension = "z"

# fslmaths ${UNIQUEID}_max_brain.nii.gz -bin ${UNIQUEID}_tissuemask
maxbiner = pe.Node(interface=maths.UnaryMaths(), name="max2binary")
maxbiner.operation = "bin"

# Generate a non-tissue mask
# fslmaths ${UNIQUEID}_tissuemask -dilM -eroF -mul -1 -add 1 -mul ${UNIQUEID}_max_func -bin -eroF ${UNIQUEID}_outofbodymask
outbodymasker = pe.Node(interface=maths.MultiImageMaths(), name="outofbodymask")
outbodymasker.inputs.op_string = "-dilM -eroF -mul -1 -add 1 -mul %s -bin -eroF"
outbodymasker.inputs.operand_files = ['_max_func']
outbodymasker._suffix = "_outofbodymask"

# Create a background image
# fslmaths ${UNIQUEID}_max_func -mul ${UNIQUEID}_tissuemask ${UNIQUEID}_backgroundimage
bgimager = pe.Node(interface=maths.MultiImageMaths(), name="backgroundimage")
bgimager.inputs.op_string = "-mul %s"
bgimager.inputs.operand_files = ['_tissuemask']
bgimager._suffix = "_backgroundimage"

# Limit input to out of body data
# fslmaths ${UNIQUEID}_prefiltered_func_data -mul ${UNIQUEID}_outofbodymask ${UNIQUEID}_OutOfBodyData
outbodier = pe.Node(interface=maths.MultiImageMaths(), name="outofbodydata")
outbodier.inputs.op_string = "-mul %s"
outbodier.inputs.operand_files = ['_outofbodymask']
outbodier._suffix = "_OutOfBodyData"

# Use melodic but turn off masking and background threshholding
# melodic -i ${UNIQUEID}_OutOfBodyData -o ${AFILE}_mcf_OutOfBody.ica --bgimage=${UNIQUEID}_backgroundimage.nii.gz --nomask --nobet --tr=${2} --mmthresh=0.5 --report
melodicor = pe.Node(interface=fsl.MELODIC(), name="Melodic")
melodicor.inputs.no_mask = True
melodicor.inputs.no_bet = True
melodicor.inputs.tr_sec = TR
melodicor.inputs.mm_thresh = 0.5
melodicor.inputs.report = True
melodicor._suffix = "_mcf_OutOfBody.ica"

# connect all fsl commands into a workflow
workflow = pe.Workflow(name="ERSN")
workflow.base_dir = "."

workflow.add_nodes([mcflirter,]) # this makes a node run independently 

workflow.connect(mcflirter, mcflirter.outputs.out_file, floater, floater.inputs.in_file)

workflow.run()
