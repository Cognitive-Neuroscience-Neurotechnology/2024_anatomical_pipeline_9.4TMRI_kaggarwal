#!/bin/bash

# Get current working directory
script_dir=$(dirname "$0")
parent_dir=$(dirname "$script_dir")

# Define output directory
subject_id=$1
# output_dir="${parent_dir}/layersim_experiment_hand_segmentation/sub-${subject_id}"
output_dir="${parent_dir}/layersim_experiment_mri_vol2vol/synthstrip_results/sub-${subject_id}"

# Create the output directory if it doesn't exist
mkdir -p "${output_dir}"

# Define input file (segmented file) path
# segmentation_file="${output_dir}/sub-${subject_id}_ses-1_manual_seg.nii"
segmentation_file="${output_dir}/sub-${subject_id}_ses-1_seg_mri_vol2vol_transformed.nii"

# Convert freesurfer segmentation values to rim
fslmaths ${segmentation_file} -thr 42 -uthr 42 -bin "${output_dir}/gm_right" -odt int
fslmaths ${segmentation_file} -thr 3 -uthr 3 -bin "${output_dir}/gm_left" -odt int
fslmaths ${segmentation_file} -thr 41 -uthr 41 -bin "${output_dir}/wm_right" -odt int
fslmaths ${segmentation_file} -thr 2 -uthr 2 -bin "${output_dir}/wm_left" -odt int
fslmaths "${output_dir}/wm_left" -add "${output_dir}/wm_right" -bin "${output_dir}/wm" -odt int
fslmaths "${output_dir}/gm_left" -add "${output_dir}/gm_right" -bin "${output_dir}/gm" -odt int
fslmaths "${output_dir}/gm" -mul 2 -add 1 -add "${output_dir}/wm" "${output_dir}/rim" -odt int

# Compute layers
LN2_LAYERS -rim "${output_dir}/rim.nii" -nr_layers 3
fslmaths "${output_dir}/rim_layers_equidist.nii" -thr 1 -uthr 1 -bin "${output_dir}/layer_deep.nii" -odt int
fslmaths "${output_dir}/rim_layers_equidist.nii" -thr 2 -uthr 2 -bin "${output_dir}/layer_middle.nii" -odt int
fslmaths "${output_dir}/rim_layers_equidist.nii" -thr 3 -uthr 3 -bin "${output_dir}/layer_superficial.nii" -odt int

# Compute columns of different sizes
LN2_COLUMNS -rim "${output_dir}/rim.nii" -midgm "${output_dir}/rim_midGM_equidist.nii" -nr_columns 100
LN2_COLUMNS -rim "${output_dir}/rim.nii" -midgm "${output_dir}/rim_midGM_equidist.nii" -nr_columns 1000
LN2_COLUMNS -rim "${output_dir}/rim.nii" -midgm "${output_dir}/rim_midGM_equidist.nii" -nr_columns 10000

# Simulate layer responses
# 1. Flat response of 2% signal change
fslmaths "${output_dir}/layer_deep.nii" -add "${output_dir}/layer_middle.nii" -add "${output_dir}/layer_superficial.nii" -mul 2 "${output_dir}/response_flat" -odt int
# 2. Increase deep
fslmaths "${output_dir}/response_flat" -add "${output_dir}/layer_deep.nii" "${output_dir}/response_deep_inc" -odt int
# 3. Decrease deep
fslmaths "${output_dir}/response_flat" -sub "${output_dir}/layer_deep.nii" "${output_dir}/response_deep_dec" -odt int
# 4. Increase superficial
fslmaths "${output_dir}/response_flat" -add "${output_dir}/layer_superficial.nii" "${output_dir}/response_superficial_inc" -odt int
# 5. Decrease superficial
fslmaths "${output_dir}/response_flat" -sub "${output_dir}/layer_superficial.nii" "${output_dir}/response_superficial_dec" -odt int
# 6. Increase middle
fslmaths "${output_dir}/response_flat" -add "${output_dir}/layer_middle.nii" "${output_dir}/response_middle_inc" -odt int
# 7. Decrease middle
fslmaths "${output_dir}/response_flat" -sub "${output_dir}/layer_middle.nii" "${output_dir}/response_middle_dec" -odt int
