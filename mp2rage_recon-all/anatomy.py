########################################
## Preprocessing Pipeline for MP2RAGE ##
########################################

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


def mprageize(inv2_file, uni_file, out_file=None):
    """ 
    Based on Sri Kashyap (https://github.com/srikash/presurfer/blob/main/func/presurf_MPRAGEise.m)
    """
    
    # Create a directory for intermediate outputs
    intermediate_dir = os.path.join(os.path.dirname(out_file), 'intermediate_outputs_mpragization')
    os.makedirs(intermediate_dir, exist_ok=True)
    
    # mprageize using temporary directory
    with TemporaryDirectory() as tmpdirname:
        copied_inv2 = os.path.join(tmpdirname, 'copied_inv2.nii')
        copied_uni = os.path.join(tmpdirname, 'copied_uni.nii')
        shutil.copyfile(inv2_file, copied_inv2)
        shutil.copyfile(uni_file, copied_uni)

        # Save input images
        nib.save(nib.load(copied_inv2), os.path.join(intermediate_dir, '01_input_inv2.nii.gz'))
        nib.save(nib.load(copied_uni), os.path.join(intermediate_dir, '01_input_uni.nii.gz'))

        # bias correct INV2
        seg = spm.NewSegment()
        seg.inputs.channel_files = copied_inv2
        seg.inputs.channel_info = (0.001, 30, (False, True))
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
        seg.inputs.write_deformation_fields = [False, False]
        seg_results = seg.run(cwd = os.path.dirname(os.path.abspath(out_file)))
        
        # Save bias corrected image
        bias_corrected_img = nib.load(seg_results.outputs.bias_corrected_images)
        nib.save(bias_corrected_img, os.path.join(intermediate_dir, '02_bias_corrected_inv2.nii.gz'))
        
        # normalize bias corrected INV2
        norm_inv2_niimg = normalize(seg_results.outputs.bias_corrected_images)
        
        # Save normalized image
        nib.save(norm_inv2_niimg, os.path.join(intermediate_dir, '03_normalized_inv2.nii.gz'))
        
        # Load UNI image
        uni_img = nib.load(copied_uni)
        uni_data = uni_img.get_fdata()
        
        # Shift and rescale UNI image
        uni_min = np.min(uni_data)
        uni_max = np.max(uni_data)
        uni_shifted = uni_data - uni_min
        uni_rescaled = uni_shifted / (uni_max - uni_min)
        
        # Save shifted and rescaled UNI image
        uni_rescaled_nii = nib.Nifti1Image(uni_rescaled, uni_img.affine, uni_img.header)
        nib.save(uni_rescaled_nii, os.path.join(intermediate_dir, '04_uni_shifted_rescaled.nii.gz'))
        
        # multiply normalized bias corrected INV2 with shifted and rescaled UNI
        mprageized_data = norm_inv2_niimg.get_fdata() * uni_rescaled
        
        # Rescale the final result to match the desired output range (e.g., 0 to 4095)
        # mprageized_rescaled = (mprageized_data - np.min(mprageized_data)) / (np.max(mprageized_data) - np.min(mprageized_data)) * 4095
        
        # Create and save the final MPRAGEized image
        mprageized_nii = nib.Nifti1Image(mprageized_data, uni_img.affine, uni_img.header)
        nib.save(mprageized_nii, out_file)
        
        # Also save it in the intermediate directory
        nib.save(mprageized_nii, os.path.join(intermediate_dir, '05_final_mprageized.nii.gz'))

        # Save image statistics
        with open(os.path.join(intermediate_dir, 'image_stats.txt'), 'w') as f:
            f.write(f"Original INV2 range: {np.min(nib.load(copied_inv2).get_fdata())} to {np.max(nib.load(copied_inv2).get_fdata())}\n")
            f.write(f"Bias corrected INV2 range: {np.min(bias_corrected_img.get_fdata())} to {np.max(bias_corrected_img.get_fdata())}\n")
            f.write(f"Normalized INV2 range: {np.min(norm_inv2_niimg.get_fdata())} to {np.max(norm_inv2_niimg.get_fdata())}\n")
            f.write(f"Original UNI range: {uni_min} to {uni_max}\n")
            f.write(f"Shifted and rescaled UNI range: {np.min(uni_rescaled)} to {np.max(uni_rescaled)}\n")
            f.write(f"Final MPRAGEized range: {np.min(mprageized_data)} to {np.max(mprageized_data)}\n")

    return mprageized_nii


def cat12_seg(in_file,cat12_output_dir):

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

        # Get current filename of the bias Corrected file
        in_file_basename = os.path.basename(os.path.abspath(in_file))
        
        # Create output directory if it does not exist
        if not os.path.exists(cat12_output_dir):
             os.makedirs(cat12_output_dir)

        # Copy data out of tmp
        shutil.copy(os.path.join(tmpdirname, 'mri', 'p1' + in_file_basename), os.path.join(cat12_output_dir, 'p1' + in_file_basename))
        shutil.copy(os.path.join(tmpdirname, 'mri', 'p2' + in_file_basename), os.path.join(cat12_output_dir, 'p2' + in_file_basename))

        # load the path of output GM and WM files from the "mri" folder into variables
        gm_file = os.path.join(cat12_output_dir, 'p1' + in_file_basename)
        wm_file = os.path.join(cat12_output_dir, 'p2' + in_file_basename)

        return gm_file, wm_file
    


def mri_synthstrip(in_file, brain_file=None):
    # Generate output filename
    brain_file = os.path.join(os.path.dirname(in_file), os.path.basename(in_file).replace('_T1w.nii', '_synthstrip_brain.nii'))
    mask_file = os.path.join(os.path.dirname(in_file), os.path.basename(in_file).replace('_T1w.nii', '_synthstrip_brain_mask.nii'))

    # Run mri_synthstrip to extract brain and create mask
    cmd = ['mri_synthstrip', '-i', in_file, '-o', brain_file, '-m', mask_file, '--no-csf']
    subprocess.run(cmd, check=True)

    # Check if the output brain file and mask file were created
    if not os.path.exists(brain_file):
        print(f"Warning: mri_synthstrip did not create {brain_file}")
    if not os.path.exists(mask_file):
        print(f"Warning: mri_synthstrip did not create {mask_file}")
    
    return brain_file, mask_file
              


def mp2rage_recon_all(inv2_file, uni_file, output_fs_dir=None, gdc_coeff_file=None, skull_strip_method=None):
    
    ##################
    ## MPRagization ##
    ##################
    # Get current working directory and filename of the loaded MP2RAGE file
    cwd = os.path.dirname(os.path.abspath(inv2_file))
    inv2_basename = str(os.path.basename(os.path.abspath(inv2_file)))
    uni_basename=str(os.path.basename(os.path.abspath(uni_file)))

    # Navigation through folders to get the path of derivatives folder where output is saved
    session_name = os.path.basename(os.path.dirname(cwd))
    subject_path = os.path.dirname(os.path.dirname(cwd))
    subject_foldername = os.path.basename(subject_path)
    orient_dep_path = os.path.dirname(os.path.dirname(os.path.dirname(cwd)))
    derivatives_path = os.path.join(orient_dep_path, 'derivatives/mp2rage_recon-all_output', subject_foldername, session_name)

    # Check if the output directory exists - if not create it
    if not os.path.exists(derivatives_path):
        os.makedirs(derivatives_path)
        print(f"****** created directory: {derivatives_path}")
    else:
        print(f"****** directory already exists: {derivatives_path}")
    
    # Create filename and path for mpragize output
    uni_mprageized_file = os.path.join(derivatives_path, subject_foldername + '_' + session_name + '_T1w.nii')

    # Perform bias correction by calling the mpragize function
    mprageize(inv2_file, uni_file, uni_mprageized_file)
    print("****** mprageize  complete")

    # run gdc
    #if gdc_coeff_file is not None:
    #    subprocess.run(['run_gdc.sh', uni_mprageized_file,  gdc_coeff_file])
    #    uni_mprageized_file = uni_mprageized_file.replace('T1w','T1w_gdc')
    #    uni_mprageized_brain_file =  uni_mprageized_brain_file.replace('T1w_brain','T1w_brain_gdc')
    #    brainmask_file = brainmask_file.replace('brainmask','brainmask_gdc')


    ####################################################
    ## Brain extraction either by CAT12 or Synthstrip ##
    ####################################################    
    # Synthstrip performs skullstripping #
    # CAT12 performs GM and WM segmentation and then combines them #
    if skull_strip_method == 'synthstrip':
        # Call mri_synthstrip function on bias corrected image
        brain_file, brainmask_filepath = mri_synthstrip(uni_mprageized_file, derivatives_path)
        print("skull removing and brain mask creation via synthstrip is complete!!!!!")
    
    elif skull_strip_method == 'cat12': 
        cat12_output_dir=os.path.join(derivatives_path,'mri')
        gm_file, wm_file = cat12_seg(uni_mprageized_file, cat12_output_dir)
        print("****** CAT12 complete")

        # Load the GM and WM files (saved by CAT12) and mprageized file
        gm_nii = nib.load(gm_file)
        wm_nii = nib.load(wm_file)
        uni_mprageized_nii = nib.load(uni_mprageized_file)
        print("****** segmentations and uni_mprageized_loaded")

        # Get data from these nifti files
        gm_data = gm_nii.get_fdata()
        wm_data = wm_nii.get_fdata()
        uni_mprageized_data = uni_mprageized_nii.get_fdata()    
        print("****** data from segmentations and uni_mprageized_data extracted")

        # Creating and saving brain mask
        brainmask_filepath = os.path.join(derivatives_path, f"{subject_foldername}_{session_name}_T1w_brainmask.nii")
        brainmask_data = np.array(((wm_data > 0) | (gm_data > 0)),dtype=int)
        brainmask_nii = nib.Nifti1Image(brainmask_data,
                                        uni_mprageized_nii.affine,
                                        uni_mprageized_nii.header)
        nib.save(brainmask_nii, brainmask_filepath)
        print("****** brain mask saved")

        # Creating and saving brain extraction
        uni_mprageized_brain_filepath = os.path.join(derivatives_path, f"{subject_foldername}_{session_name}_T1w_brain.nii")
        uni_mprageized_brain_data = brainmask_data * uni_mprageized_data
        uni_mprageized_brain_nii = nib.Nifti1Image(uni_mprageized_brain_data,
                                                uni_mprageized_nii.affine,
                                                uni_mprageized_nii.header)
        nib.save(uni_mprageized_brain_nii, uni_mprageized_brain_filepath)
        print("****** brain extraction saved")
    else:
        raise ValueError("Invalid skull stripping method. Choose either 'synthstrip' or 'cat12'.")


    ##########################################
    ##### run recon-all from Freesurfer ######
    ##########################################

    # define directory for Freeseurfer
    fs_dir = derivatives_path
    sub = 'freesurfer'
        
    # autorecon1 without skullstrip removal (~11 mins) - added -gcut flag to exclude dura
    os.system("recon-all" + \
          " -i " + uni_mprageized_file + \
          " -hires" + \
          " -autorecon1" + \
          " -noskullstrip" + \
          " -gcut" + \
          " -sd " + fs_dir + \
          " -s " + sub + \
          " -parallel")
    print("****** auto recon 1 is complete")

    # apply brain mask from CAT12 or synthstrip
    transmask = ApplyVolTransform()
    transmask.inputs.source_file = brainmask_filepath
    transmask.inputs.target_file = os.path.join(fs_dir, sub, 'mri', 'orig.mgz')
    transmask.inputs.reg_header = True
    transmask.inputs.interp = "nearest"
    transmask.inputs.transformed_file = os.path.join(fs_dir, sub, 'mri', 'brainmask_mask.mgz')
    transmask.inputs.args = "--no-save-reg"
    transmask.run(cwd=cwd)
    print("****** applying brain mask from CAT12 or synthstrip is complete")

    applymask = ApplyMask()
    applymask.inputs.in_file = os.path.join(fs_dir, sub,'mri','T1.mgz')
    applymask.inputs.mask_file = os.path.join(fs_dir, sub, 'mri', 'brainmask_mask.mgz')
    applymask.inputs.out_file =  os.path.join(fs_dir, sub, 'mri', 'brainmask.mgz')
    applymask.run(cwd=cwd)
    print("****** apply mask is complete")

    shutil.copy2(os.path.join(fs_dir, sub, 'mri', 'brainmask.mgz'),
                 os.path.join(fs_dir, sub, 'mri', 'brainmask.auto.mgz'))

    # continue recon-all
    with open(os.path.join(derivatives_path,'expert.opts'), 'w') as text_file:
        text_file.write('mris_inflate -n 100\n')
        print("****** expert option saved as text file")
    
    # autorecon 2 and 3 - added -gcut flag to exclude dura
    os.system("recon-all" + \
              " -hires" + \
              " -autorecon2" + " -autorecon3"\
              " -gcut" + \
              " -sd " + fs_dir + \
              " -s " + sub + \
              " -expert " + os.path.join(derivatives_path,'expert.opts') + \
              " -xopts-overwrite" + \
              " -parallel")
    print("****** auto recon 2 and 3 are complete")
