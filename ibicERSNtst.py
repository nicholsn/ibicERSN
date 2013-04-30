"""
IBIC Extract Remove Scanner Noise
"""
__author__ = 'Nolan Nichols <nolan.nichols@gmail.com>'

import os
import re
import glob

import pandas as pd

import matplotlib.pyplot as plt

import nipype.interfaces.fsl as fsl
import nipype.interfaces.fsl.maths as maths
import nipype.pipeline.engine as pe

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

# TODO: Look into betsurf to find scalp boundry (bet fmri.nii.gz fmri_brain.nii.gz -A

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
workflow.connect([(mcflirter, floater,
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


def get_melodicdata(melodic_dir, data_type="timeseries"):
    """
    Compile all timecourse components
    melodic_dir = melodic directry (str)
    ts_type = type of timeseries to extract (timeseries or freqpower) 
    """

    def natural_key(astr):
        """
        Sort strings ending in integers using a natural numerical order
        See http://stackoverflow.com/questions/34518/natural-sorting-algorithm
        """
        return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', astr)]

    TS_TYPE = None
    if data_type == "timeseries":
        TS_TYPE = "t"
    elif data_type == "freqpower":
        TS_TYPE = "f"
    else:
        print "Please choose a supported data_type [timeseries, freqpower]"

    melodic_dir = os.path.abspath(melodic_dir)
    ts_files = glob.glob(os.path.join(melodic_dir, 'report/' + TS_TYPE + '*.txt'))
    ts_files.sort(key=natural_key)

    # keep the timecourse order
    ts_frame = pd.DataFrame()
    for ts_index, ts_file in enumerate(ts_files):
        ts_index += 1
        ts_series = pd.read_csv(ts_file, header=None, names=[TS_TYPE + str(ts_index)])
        if ts_frame.empty:
            ts_frame = ts_series
        else:
            ts_frame = ts_frame.join(ts_series)
    data_filename = os.path.join(melodic_dir, "report/" + data_type + "data.csv")
    ts_frame.to_csv(data_filename, header=False, index=False)
    print "wrote file: " + data_filename
    return data_filename


def plot_scannernoiseenvelope(timeseriesdata, spike_thresh=None, savefig=True):
    """
    plot the scanner noise envelope
    timeseriesdata : csv file of ica time series
    spike_thresh   : normalized response threshold for spike identification
    savefig        : save ScannerNoiseEnvelope.png
    """

    # load the timeseries
    ts = pd.read_csv(timeseriesdata)

    # count the number of ICs
    number_of_ics = ts.columns.size

    # get an index to the ICs with spikes
    ic_max = ts.max()
    if spike_thresh is None:
        spike_thresh = 4 # default is 4
    spikes = ic_max[ic_max > spike_thresh]

    ## Plotting the ScannerNoiseEnvelope ##

    # get the max value across ICs at each timepoint
    top = ts.T.max()
    bottom = ts.T.min()

    # plot labels
    plt.title("Scanner Noise Envelope for file: %s" % timeseriesdata)
    plt.xlabel("Volumes")
    plt.ylabel("Normalized Response")

    # plot scaling
    plt.xlim(0, top.size)

    # draw the plot by filling the space between the top and bottom values 
    plt.fill_between(top.size, top.values, bottom.values)

    # could also do a layover of spiked ICs and add them to a legend key
    # for ic_idx in spikes.keys():
    #     plt.plot(ts[ic_idx], color='r')

    # save the figure 
    if savefig is True:
        envelope_png = os.path.join(melodic_dir, "report/", 'ScannerNoiseEnvelope.png')
        plt.savefig(envelope_png, format='png')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.description = "IBIC Extract Remove Scanner Noise (ERSN) Utility"

    workflow.write_graph()
    workflow.run()
    workflow.run(plugin='MultiProc', plugin_args={'n_procs': 2})