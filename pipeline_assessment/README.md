This folder has all the scripts for pipeline assessment using the layer response simulation method.

Follow these steps first to prepare the data for pipeline assessment:

**Steps for processing hand segmentation data:**

1. Copy the manual segmentation from the UHC dataset to the layersim_experiment/layersim_experiment_hand_segmentation/sub-{id} path

2. Rename the file from "sub-3_ses-1_seg.nii" to "sub-3_ses-1_manual_seg.nii"

3. Check the file path in the "prepare_layer_sim.sh" and "parallel_prepare_layer_sim.sh" scripts. It should be hand_segmentation path (line 9,16 and 28 respectively)

4. Run the "parallel_prepare_layer_sim.sh" script.

5. After running prepare_layer_sim.sh script (laynii on hand segmentation and performing simulation of responses), we need to smooth the responses as well. To perform the smoothing, follow this command (create a folder smoothed_responses):

fslmaths response_flat.nii.gz -s 0.42553 smoothed_responses/response_flat.nii.gz
fslmaths response_superficial_inc.nii.gz -s 0.42553 smoothed_responses/response_superficial_inc.nii.gz
fslmaths response_superficial_dec.nii.gz -s 0.42553 smoothed_responses/response_superficial_dec.nii.gz
fslmaths response_middle_inc.nii.gz -s 0.42553 smoothed_responses/response_middle_inc.nii.gz
fslmaths response_middle_dec.nii.gz -s 0.42553 smoothed_responses/response_middle_dec.nii.gz
fslmaths response_deep_inc.nii.gz -s 0.42553 smoothed_responses/response_deep_inc.nii.gz
fslmaths response_deep_dec.nii.gz -s 0.42553 smoothed_responses/response_deep_dec.nii.gz

**Steps followed after running mp2rage_recon-all pipeline:**

1. Copy the aseg.mgz file to the layersim_experiment_mri_vol2vol/sub-{id} folder

2. After copying, run mri_vol2vol command for transformation:
mri_vol2vol --mov aseg.mgz --targ /ptmp/kaggarwal/layersim_experiment/layersim_experiment_hand_segmentation/sub-46/sub-46_ses-1_manual_seg.nii --regheader --o sub-46_ses-1_cat12_seg_mri_vol2vol_transformed.mgz --no-save-reg --interp nearest

3. Then run mri_convert command for converting .mgz format to .nii format:
mri_convert input.mgz output.nii

4. Check the file path in the "prepare_layer_sim.sh" and "parallel_prepare_layer_sim.sh" scripts. It should be mri_vol2vol path (line 10,17 and 29 respectively)

5. Run the "parallel_prepare_layer_sim.sh" script.

6. Copy the aparc+aseg.mgz file from freesurfer/mri of each subject to layersim_experiment_mri_vol2vol (This is required for creating lobes)

7. After copying, run mri_vol2vol command for transformation:
mri_vol2vol --mov aparc+aseg.mgz --targ /ptmp/kaggarwal/layersim_experiment/layersim_experiment_hand_segmentation/sub-46/sub-46_ses-1_manual_seg.nii --regheader --o aparc+aseg_transformed.mgz --no-save-reg --interp nearest

8. Then run mri_convert command for converting .mgz format to .nii format:
mri_convert input.mgz output.nii


**Scripts in this folder are then to be run in the following sequence:**
1. Layer simulation
2. Layer profile calculation v2
3. Layer profile calculation v3
4. Layer profile visualization v2
5. Layer profile visualization v3
6. Metrics calculation
7. GLM

