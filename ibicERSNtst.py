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
mcflirter = pe.Node(interface=fsl.MCFLIRT(), name="Mcflirt")

# Generate a tissue mask
# fslmaths ${AFILE}_mcf ${UNIQUEID}_prefiltered_func_data -odt float
floater = pe.Node(interface=maths.ChangeDataType(), name="Mcf2float")
floater.inputs.output_datatype = "float"

# fslmaths ${UNIQUEID}_prefiltered_func_data -Tmax ${UNIQUEID}_max_func
tmaxer = pe.Node(interface=maths.MaxImage(), name="Tmax")
tmaxer.dimension = "T"

# bet ${AFILE}_mcf.nii.gz ${UNIQUEID}_brain.nii.gz
better = pe.Node(interface=fsl.BET(), name="Bet")

# fslmaths ${UNIQUEID}_brain.nii.gz -bin -kernel gauss 12 -ero -ero ${UNIQUEID}_brain_e2.nii.gz
eroder = pe.Node(interface=maths.MathsCommand(), name="Erode")
eroder.inputs.args = "-bin -kernel gauss 12 -ero -ero"

# fslmaths ${UNIQUEID}_brain_e2.nii.gz -kernel gauss 12 -dilM -dilM -dilM ${UNIQUEID}_brain_e2d3.nii.gz
dilator = pe.Node(interface=maths.MathsCommand(), name="Dilate")
dilator.inputs.args = "-kernel gauss 12 -dilM -dilM -dilM"

# fslsplit ${UNIQUEID}_brain_e2d3.nii.gz temp_slice -z
splitter = pe.Node(interface=fsl.Split(), name="Split")
splitter.inputs.dimension = "z"
splitter.inputs.out_base_name = "temp_slice"

# fslmaths ${UNIQUEID}_brain_e2d3.nii.gz -Zmax temp_base.nii.gz
zmaxer = pe.MapNode(interface=maths.MaxImage(), name="Zmax", iterfield=['in_file'])
zmaxer.dimension = "Z"

# fslmerge -z ${UNIQUEID}_max_brain.nii.gz ${mergelist}
merger = pe.Node(interface=fsl.Merge(), name="Merge")
merger.inputs.dimension = "z"

# fslmaths ${UNIQUEID}_max_brain.nii.gz -bin ${UNIQUEID}_tissuemask
maxbiner = pe.Node(interface=maths.UnaryMaths(), name="Max2binary")
maxbiner.inputs.operation = "bin"

# Generate a non-tissue mask
# fslmaths ${UNIQUEID}_tissuemask -dilM -eroF -mul -1 -add 1 -mul ${UNIQUEID}_max_func -bin -eroF ${UNIQUEID}_outofbodymask
outbodymasker = pe.Node(interface=maths.MultiImageMaths(), name="Outofbodymask")
outbodymasker.inputs.op_string = "-dilM -eroF -mul -1 -add 1 -mul %s -bin -eroF"

# Create a background image
# fslmaths ${UNIQUEID}_max_func -mul ${UNIQUEID}_tissuemask ${UNIQUEID}_backgroundimage
bgimager = pe.Node(interface=maths.MultiImageMaths(), name="Backgroundimage")
bgimager.inputs.op_string = "-mul %s"

# Limit input to out of body data
# fslmaths ${UNIQUEID}_prefiltered_func_data -mul ${UNIQUEID}_outofbodymask ${UNIQUEID}_OutOfBodyData
outbodier = pe.Node(interface=maths.MultiImageMaths(), name="outofbodydata")
outbodier.inputs.op_string = "-mul %s"

# Use melodic but turn off masking and background threshholding
# melodic -i ${UNIQUEID}_OutOfBodyData -o ${AFILE}_mcf_OutOfBody.ica --bgimage=${UNIQUEID}_backgroundimage.nii.gz --nomask --nobet --tr=${2} --mmthresh=0.5 --report
melodicor = pe.Node(interface=fsl.MELODIC(), name="Melodic")
melodicor.inputs.no_mask = True
melodicor.inputs.no_bet = True
melodicor.inputs.tr_sec = TR
melodicor.inputs.mm_thresh = 0.5
melodicor.inputs.report = True

# connect all fsl commands into a workflow
workflow = pe.Workflow(name="ERSN")
workflow.base_dir = "."

# connect mcflirter to floater
workflow.connect([(mcflirter,floater, 
                   [("out_file", "in_file")])])

# connect floater to tmaxer
workflow.connect([(floater, tmaxer,
                   [("out_file", "in_file")])])

# connect mcflirter to better
workflow.connect([(mcflirter, better,
                   [("out_file", "in_file")])])

# connect better to eroder
workflow.connect([(better, eroder,
                   [("out_file", "in_file")])])

# connect eroder to dilator
workflow.connect([(eroder, dilator,
                   [("out_file", "in_file")])])

# connect dilator to splitter
workflow.connect([(dilator, splitter,
                   [("out_file", "in_file")])])

# connect splitter to zmaxer
workflow.connect([(splitter, zmaxer,
                   [("out_files", "in_file")])])

# connect zmaxer to merger
workflow.connect([(zmaxer, merger,
                   [("out_file", "in_files")])])

# connect zmaxer to merger
workflow.connect([(merger, maxbiner,
                   [("merged_file", "in_file")])])

# connect maxbiner and tmaxer to to outbodymasker
workflow.connect([(maxbiner, outbodymasker,
                   [("out_file", "in_file")]),
                  (tmaxer, outbodymasker,
                      [('out_file', 'operand_files')])])

# connect tmaxer and maxbiner to bgimager
workflow.connect([(tmaxer, bgimager,
                   [("out_file", "in_file")]),
                  (maxbiner, bgimager,
                   [('out_file', 'operand_files')])])

# connect tmaxer and maxbiner to outbodier
workflow.connect([(floater, outbodier,
                   [("out_file", "in_file")]),
                  (outbodymasker, outbodier,
                   [('out_file', 'operand_files')])])

# connect outbodier and bgimager to melodicor
workflow.connect([(outbodier, melodicor,
                   [("out_file", "in_files")]),
                  (bgimager, melodicor,
                   [('out_file', 'bg_image')])])

if __name__ == '__main__':
    workflow.write_graph()
    workflow.run()
    workflow.run(plugin='MultiProc', plugin_args={'n_procs':2})