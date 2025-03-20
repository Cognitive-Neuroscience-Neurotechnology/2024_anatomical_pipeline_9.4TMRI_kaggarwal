#!/bin/bash
subject=sub-29
out_dir=$(pwd)/data

simdata_dir=/ptmp/kaggarwal/layersim_experiment
handseg_sim_dir=${simdata_dir}/layersim_experiment_hand_segmentation/${subject}
pipeline_sim_dir=${simdata_dir}/layersim_experiment_mri_vol2vol/${subject}
anatdata_dir=/ptmp/kaggarwal/BIDS_data/2024_9T_AnatomicalPipeline/Ultracortex_v1.1.0
pipeline_output_dir=${anatdata_dir}/derivatives/mp2rage_recon-all_output_cat12_for_simulation/${subject}/ses-1


# background T1w
background_anat=${pipeline_output_dir}/${subject}_ses-1_T1w.nii

# segmented GM ribbon
gm_hand=${handseg_sim_dir}/gm.nii
gm_pipeline=${pipeline_sim_dir}/gm.nii.gz

# columns (for masking only) - NOTE: should also be smoothed!
columns_hand=${handseg_sim_dir}/rim_columns100.nii

# layers
layers_hand=${handseg_sim_dir}/rim_layers_equidist.nii
layers_pipeline=${pipeline_sim_dir}/rim_layers_equidist.nii

# response
response_hand=${handseg_sim_dir}/response_middle_inc.nii

# smoothed response
response_hand_smoothed=${handseg_sim_dir}/smoothed_responses/response_middle_inc.nii.gz

export FSLOUTPUTTYPE=NIFTI



## proposed scheme:
# 0. generate a simulation roi mask by selecting from the hand-segmented columns
col_idx=33
fslmaths ${columns_hand} -thr ${col_idx} -uthr ${col_idx} -bin ${out_dir}/simroi.nii
# 1. generate a response localized to simulation roi
fslmaths ${response_hand} -mas ${out_dir}/simroi.nii ${out_dir}/roi_response.nii
fslmaths ${out_dir}/roi_response.nii -s 0.42553 ${out_dir}/roi_response_smoothed.nii


# for each segmentation sample all non-zero responses according to segmentation-dependent layering
fslmaths ${out_dir}/roi_response_smoothed.nii -thr 0 -bin ${out_dir}/roi_response_mask.nii
LN2_PROFILE -layers ${layers_hand} -input ${out_dir}/roi_response.nii -mask ${out_dir}/roi_response_mask.nii \
    -output ${out_dir}/handseg_profile


fslmaths ${out_dir}/roi_response_smoothed.nii -thr 0 -bin ${out_dir}/roi_response_mask.nii
LN2_PROFILE -layers ${layers_pipeline} -input ${out_dir}/roi_response.nii -mask ${out_dir}/roi_response_mask.nii \
    -output ${out_dir}/pipeline_profile

# fsleyes ${T1w} ${response_hand} ${columns_handseg} ${out_dir}/simroi.nii ${out_dir}/roi_response.nii ${out_dir}/roi_response_smoothed.nii \
#     ${out_dir}/roi_response_mask.nii ${layers_handseg} ${layers_pipeline}
    
