#!/bin/bash

# Define base paths
base_source_path="/home/kaggarwal/ptmp/BIDS_data/2024_9T_AnatomicalPipeline/Ultracortex_v1.1.0/derivatives/mp2rage_recon-all_output_synthstrip_for_simulation"
destination_folder="/home/kaggarwal/ptmp/layersim_experiment/layersim_experiment_mri_vol2vol/synthstrip_results"
man_seg_base_path="/ptmp/kaggarwal/layersim_experiment/layersim_experiment_hand_segmentation"

# List of subjects
subjects=("sub-3" "sub-9" "sub-20" "sub-29" "sub-44" "sub-46")

# Loop over subjects
for subject in "${subjects[@]}"; do

  # Define paths for aseg.mgz and manual segmentation
  source_file="$base_source_path/$subject/ses-1/freesurfer/mri/aseg.mgz"
  subject_destination="$destination_folder/$subject"
  manual_seg="$man_seg_base_path/${subject}/${subject}_ses-1_manual_seg.nii"
  output_transformed="${subject}_ses-1_seg_mri_vol2vol_transformed.mgz"

  # Create subject folder and copy aseg.mgz
  mkdir -p "$subject_destination"
  cp "$source_file" "$subject_destination"
  echo "Copied $source_file to $subject_destination"

  # Run mri_vol2vol for aseg.mgz
  cd "$subject_destination"
  mri_vol2vol --mov aseg.mgz --targ "$manual_seg" --regheader --o "$output_transformed" --no-save-reg --interp nearest
  echo "Transformation with mri_vol2vol completed for $subject aseg.mgz"

  # Convert .mgz to .nii
  mri_convert "$output_transformed" "${output_transformed%.mgz}.nii"
  echo "Converted $output_transformed to .nii format"

  # Copy aparc+aseg.mgz
  aparc_source_file="$base_source_path/$subject/ses-1/freesurfer/mri/aparc+aseg.mgz"
  aparc_output_transformed="${subject}_ses-1_aparc+aseg_transformed.mgz"
  cp "$aparc_source_file" "$subject_destination"
  echo "Copied $aparc_source_file to $subject_destination"

  # Run mri_vol2vol for aparc+aseg.mgz
  mri_vol2vol --mov "aparc+aseg.mgz" --targ "$manual_seg" --regheader --o "$aparc_output_transformed" --no-save-reg --interp nearest
  echo "Transformation with mri_vol2vol completed for $subject aparc+aseg.mgz"

  # Convert aparc+aseg_transformed.mgz to .nii
  mri_convert "$aparc_output_transformed" "${aparc_output_transformed%.mgz}.nii"
  echo "Converted $aparc_output_transformed to .nii format"

done

echo "All tasks completed successfully for all subjects."