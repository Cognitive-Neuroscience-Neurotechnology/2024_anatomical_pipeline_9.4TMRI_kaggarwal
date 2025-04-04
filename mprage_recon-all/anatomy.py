#######################################
## Preprocessing Pipeline for MPRAGE ##
#######################################

from nipype.interfaces import spm
from nipype.interfaces import matlab
from nipype.interfaces import cat12
from nipype.interfaces.freesurfer import ApplyVolTransform, ApplyMask
import nipype.pipeline.engine as pe
import nibabel as nib
import numpy as np
import os
import sys
import gzip
import shutil
import subprocess
from tempfile import TemporaryDirectory
import tempfile


matlab_cmd = '/opt/spm12/run_spm12.sh /opt/mcr/v93 script'
spm_path = '/opt/spm12/spm12_mcr/home/gaser/gaser/spm/spm12'
spm.SPMCommand.set_mlab_paths(matlab_cmd=matlab_cmd, use_mcr=True)

def set_spm_path(new_spm_path):
    global spm_path
    spm_path = new_spm_path
    matlab.MatlabCommand.set_default_paths(spm_path)

def check_spm_path():
    print(spm_path)
    
def load_niimg(niimg):
    if type(niimg) is str:
        return nib.load(niimg)
    else:
        return niimg

def normalize(niimg_in,out_file=None):
    niimg_in = load_niimg(niimg_in)
    data = niimg_in.get_fdata()
    data_norm = (data-np.min(data))/(np.max(data)-np.min(data))
    niimg_out = nib.Nifti1Image(data_norm,niimg_in.affine,niimg_in.header)
    if out_file:
        nib.save(niimg_out,out_file)
    return niimg_out

def multiply(niimg_in1, niimg_in2, out_file=None):
    niimg_in1 = load_niimg(niimg_in1)
    niimg_in2 = load_niimg(niimg_in2)
    data1 = niimg_in1.get_fdata()
    data2 = niimg_in2.get_fdata()
    data_mult = data1 * data2
    niimg_out = nib.Nifti1Image(data_mult,niimg_in1.affine,niimg_in1.header)
    if out_file:
        nib.save(niimg_out,out_file)
    return niimg_out


def bias_correction(mprage_file, out_file = None):

    # Check if the input file exists
    if not os.path.exists(mprage_file):
        raise FileNotFoundError(f"Input file not found: {mprage_file}")
    
    # Check .nii and .nii.gz extension and unzip if .nii.gz
    if mprage_file.endswith('.nii.gz'):
        nii_file = mprage_file[:-3]
        
        with gzip.open(mprage_file, 'rb') as f_in:
            with open(nii_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    elif mprage_file.endswith('.nii'):
        nii_file = mprage_file
    else:
        raise ValueError(f"Unsupported file format: {mprage_file}. Please use .nii or .nii.gz files.")

    # Bias correction using Temporary directory
    with TemporaryDirectory() as tmpdirname:
        copied_input = os.path.join(tmpdirname, 'copied_input.nii')
        shutil.copyfile(nii_file, copied_input)

        # Create SPM object with specific parameters
        seg = spm.NewSegment()
        seg.inputs.channel_files = copied_input
        seg.inputs.channel_info = (0.001, 40, (False, True))
        tissue1 = ((os.path.join(spm_path,'tpm','TPM.nii'), 1), 2, (False,False), (False, False))
        tissue2 = ((os.path.join(spm_path,'tpm','TPM.nii'), 2), 2, (False,False), (False, False))
        tissue3 = ((os.path.join(spm_path,'tpm','TPM.nii'), 3), 2, (False,False), (False, False))
        tissue4 = ((os.path.join(spm_path,'tpm','TPM.nii'), 4), 3, (False,False), (False, False))
        tissue5 = ((os.path.join(spm_path,'tpm','TPM.nii'), 5), 4, (False,False), (False, False))
        tissue6 = ((os.path.join(spm_path,'tpm','TPM.nii'), 6), 2, (False,False), (False, False))
        seg.inputs.tissues = [tissue1, tissue2, tissue3, tissue4, tissue5, tissue6]
        seg.inputs.affine_regularization = 'mni'
        seg.inputs.sampling_distance = 3
        seg.inputs.warping_regularization = [0, 0.001, 0.5, 0.05, 0.2]
        seg.inputs.write_deformation_fields = [True, True]

        # Perform bias correction
        seg_results = seg.run(cwd = os.path.dirname(os.path.abspath(out_file)))

        # Extract the path of the bias correction from seg_results
        bc_mprage_file = seg_results.outputs.bias_corrected_images

        # Load the output path and then save it to the destination folder
        bias_corrected_img = nib.load(bc_mprage_file)
        nib.save(bias_corrected_img, out_file)

        return bias_corrected_img



def cat12_seg(in_file, cat12_output_dir):

    # CAT12 segmentation using temporary memory
    with TemporaryDirectory() as tmpdirname:
        copied_input = os.path.join(tmpdirname, os.path.basename(in_file))
        shutil.copyfile(in_file, copied_input)
    
        # Load the bias corrected image 
        img = nib.load(copied_input)

        # Calculate median of resolution - to be used by CAT12 object
        median_res = np.median(img.header.get_zooms()[:3])
        
        # Create CAT12 object with specific parameters
        cat12_segment = cat12.CAT12Segment(in_files = copied_input)
        cat12_segment.inputs.internal_resampling_process = (median_res, 0.1)
        cat12_segment.inputs.surface_and_thickness_estimation = 0
        cat12_segment.inputs.surface_measures = 0
        cat12_segment.inputs.neuromorphometrics = False
        cat12_segment.inputs.lpba40 = False
        cat12_segment.inputs.cobra = False
        cat12_segment.inputs.hammers = False
        cat12_segment.inputs.gm_output_native = True    
        cat12_segment.inputs.gm_output_modulated = False
        cat12_segment.inputs.gm_output_dartel = False
        cat12_segment.inputs.wm_output_native = True    
        cat12_segment.inputs.wm_output_modulated = False
        cat12_segment.inputs.wm_output_dartel = False
        cat12_segment.inputs.csf_output_native = True    
        cat12_segment.inputs.csf_output_modulated = False
        cat12_segment.inputs.csf_output_dartel = False
        cat12_segment.inputs.jacobianwarped = False
        cat12_segment.inputs.label_warped = False
        cat12_segment.inputs.las_warped = False
        cat12_segment.inputs.save_bias_corrected = False
        cat12_segment.inputs.warps = (0, 0)
        cat12_segment.inputs.output_labelnative = True
        # cat12_segment.inputs.output_surface = False
        # cat12_segment.inputs.no_surf = True
        cat12_segment.run(cwd = tmpdirname) 

        # Get current working directory and filename of the loaded Bias Corrected file
        # cwd = os.path.dirname(os.path.abspath(in_file))
        in_file_basename = os.path.basename(os.path.abspath(in_file))

        # Create output directory if it doesn't exist
        if not os.path.exists(cat12_output_dir):
            os.makedirs(cat12_output_dir)
        
        # Copy data out of temp
        shutil.copy(os.path.join(tmpdirname, 'mri', 'p1' + in_file_basename), os.path.join(cat12_output_dir, 'p1' + in_file_basename))
        shutil.copy(os.path.join(tmpdirname, 'mri', 'p2' + in_file_basename), os.path.join(cat12_output_dir, 'p2' + in_file_basename))

        # Load the path of output GM and WM files from the "mri" folder into variables
        gm_file = os.path.join(cat12_output_dir, 'p1' + in_file_basename)
        wm_file = os.path.join(cat12_output_dir, 'p2' + in_file_basename)

        return gm_file, wm_file



def mri_synthstrip(in_file, brain_file=None):
    # Generate output filename
    brain_file = os.path.join(os.path.dirname(in_file), os.path.basename(in_file).replace('_mprage_bc.nii', '_synthstrip_brain.nii'))
    mask_file = os.path.join(os.path.dirname(in_file), os.path.basename(in_file).replace('_mprage_bc.nii', '_synthstrip_brain_mask.nii'))

    # Run mri_synthstrip to extract brain and create mask
    cmd = ['mri_synthstrip', '-i', in_file, '-o', brain_file, '-m', mask_file, '--no-csf']
    subprocess.run(cmd, check=True)

    # Check if the output brain file and mask file were created
    if not os.path.exists(brain_file):
        print(f"Warning: mri_synthstrip did not create {brain_file}")
    if not os.path.exists(mask_file):
        print(f"Warning: mri_synthstrip did not create {mask_file}")
    
    return brain_file, mask_file




def mprage_recon_all(mprage_file = None, skull_strip_method=None):
    
    #####################
    ## Bias correction ##
    #####################
    # Get current working directory and filename of the loaded MPRAGE file
    cwd = os.path.dirname(os.path.abspath(mprage_file))
    mprage_basename = str(os.path.basename(os.path.abspath(mprage_file)))

    # Navigation through folders to get the path of derivatives folder where output is saved
    session_name = os.path.basename(os.path.dirname(cwd))
    subject_path = os.path.dirname(os.path.dirname(cwd))
    subject_foldername = os.path.basename(subject_path)
    orient_dep_path = os.path.dirname(os.path.dirname(os.path.dirname(cwd)))
    derivatives_path = os.path.join(orient_dep_path, 'derivatives/mprage_recon-all_output', 
                                    subject_foldername, session_name)

    # Check if the output directory exists - if not create it
    if not os.path.exists(derivatives_path):
        os.makedirs(derivatives_path)
        print(f"*********** Created directory: {derivatives_path}")
    else:
        print(f"*********** Directory already exists: {derivatives_path}")
    
    # Create filename and path for the bias corrected image
    bc_mprage_file = os.path.join(derivatives_path, subject_foldername + '_' + session_name + '_mprage_bc.nii') 
    
    # Perform bias correction by calling the function
    bias_correction(mprage_file, bc_mprage_file)
    print("************* Bias Correction complete! - Check the Derivatives folder")


    ####################################################
    ## Brain extraction either by CAT12 or Synthstrip ##
    ####################################################
    # Synthstrip performs skullstripping #
    # CAT12 performs GM and WM segmentation and then combines them #
    if skull_strip_method == 'synthstrip':
        # Call mri_synthstrip function on bias corrected image
        brain_file, brainmask_filepath = mri_synthstrip(bc_mprage_file, derivatives_path)
        print("skull removing and brain mask creation via synthstrip is complete!!!!!")
    elif skull_strip_method == 'cat12': 
        # Call CAT12 function on bias corrected image
        cat12_output_dir = os.path.join(derivatives_path, 'mri')
        gm_file, wm_file = cat12_seg(bc_mprage_file, cat12_output_dir)
        print("************ CAT12 complete!!!!")  

        # Load the GM and WM files (saved by CAT12) and Bias corrected file
        gm_nii = nib.load(gm_file)
        wm_nii = nib.load(wm_file)
        bc_mprage_nii = nib.load(bc_mprage_file)
        print("************ segmentations and bias correction loaded")

        # Get data from these NIFTI files
        gm_data = gm_nii.get_fdata()
        wm_data = wm_nii.get_fdata()
        bc_mprage_data = bc_mprage_nii.get_fdata()
        print("************ data from segmentations and bias correction extracted")

        # Creating and saving brain mask
        brainmask_filepath = os.path.join(derivatives_path, f"{subject_foldername}_{session_name}_brain_mask.nii")
        brainmask_data = np.array(((wm_data > 0) | (gm_data > 0)),dtype=int)
        brainmask_nii = nib.Nifti1Image(brainmask_data,
                                        bc_mprage_nii.affine,
                                        bc_mprage_nii.header)
        nib.save(brainmask_nii, brainmask_filepath)
        print("Brain mask saved")

        # Creating and saving brain extraction
        bc_brain_filepath = os.path.join(derivatives_path, f"{subject_foldername}_{session_name}_bc_brain.nii")
        brain_data = brainmask_data * bc_mprage_data
        brain_nii = nib.Nifti1Image(brain_data, 
                                    bc_mprage_nii.affine, 
                                    bc_mprage_nii.header)
        nib.save(brain_nii, bc_brain_filepath)
        print("Brain extraction saved")
    else:
        raise ValueError("Invalid skull stripping method. Choose either 'synthstrip' or 'cat12'.")


    ###############################
    ## recon-all from Freesurfer ##
    ###############################
    # Define directory for Freeseurfer
    fs_dir = derivatives_path
    sub = 'freesurfer'
        
    # autorecon1 without skullstrip removal
    os.system("recon-all" + \
          " -i " + bc_mprage_file + \
          " -hires" + \
          " -autorecon1" + \
          " -noskullstrip" + \
          " -sd " + fs_dir + \
          " -s " + sub + \
          " -parallel")
    print("*********** Auto recon 1 is complete")

    # apply brain mask from CAT12
    transmask = ApplyVolTransform()
    transmask.inputs.source_file = brainmask_filepath
    transmask.inputs.target_file = os.path.join(fs_dir, sub, 'mri', 'orig.mgz')
    transmask.inputs.reg_header = True
    transmask.inputs.interp = "nearest"
    transmask.inputs.transformed_file = os.path.join(fs_dir, sub, 'mri', 'brainmask_mask.mgz')
    transmask.inputs.args = "--no-save-reg"
    transmask.run(cwd=cwd)
    print("************* Applying brain mask from CAT12 is complete")

    applymask = ApplyMask()
    applymask.inputs.in_file = os.path.join(fs_dir, sub,'mri','T1.mgz')
    applymask.inputs.mask_file = os.path.join(fs_dir, sub, 'mri', 'brainmask_mask.mgz')
    applymask.inputs.out_file =  os.path.join(fs_dir, sub, 'mri', 'brainmask.mgz')
    applymask.run(cwd=cwd)
    print("************** Apply Mask is complete")


    shutil.copy2(os.path.join(fs_dir, sub, 'mri', 'brainmask.mgz'),
                 os.path.join(fs_dir, sub, 'mri', 'brainmask.auto.mgz'))

    # continue recon-all
    with open(os.path.join(derivatives_path,'expert.opts'), 'w') as text_file:
        text_file.write('mris_inflate -n 100\n')
        print("****** expert option saved as text file")

    # autorecon 2 and 3
    os.system("recon-all" + \
              " -hires" + \
              " -autorecon2" + " -autorecon3"\
              " -sd " + fs_dir + \
              " -s " + sub + \
              " -expert " + os.path.join(derivatives_path,'expert.opts') + \
              " -xopts-overwrite" + \
              " -parallel")
    print("************** Auto recon 2 and 3 are complete")
