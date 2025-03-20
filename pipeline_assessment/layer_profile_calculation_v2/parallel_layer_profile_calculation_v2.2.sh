#!/bin/bash -l

##############################
#       Job blueprint        #
##############################

#### define some basic SLURM properties for this job
#SBATCH --job-name=layer_profile_calculation_v2.2
#SBATCH --output=layer_profile_calculation_v2.2_%A_%a.out
#SBATCH --error=layer_profile_calculation_v2.2_%A_%a.err
#SBATCH --partition=compute
#SBATCH --array=1-42
#SBATCH --time=4:00:00  
#SBATCH --mem=5GB  

# Define environment
container=/ptmp/kaggarwal/containers/gfae.sif 
MINICONDA_PATH=/opt/conda/bin/activate 

# Define data directory
studyDataDir=/home/kaggarwal/ptmp/layersim_experiment

# Extract the responses from config file
config_file="config.txt"
line=$(sed -n "$SLURM_ARRAY_TASK_ID"p "$config_file")
subject_id=$(echo "$line" | awk '{print $1}')
response=$(echo "$line" | awk '{print $2}')

echo "Processing subject: ${subject}"
echo "Processing response: ${response}"

## Run the Python script inside the container - Pipeline Output
srun apptainer exec ${container} bash -c \
"source ${MINICONDA_PATH} && python ${studyDataDir}/layer_profile_calculation_v2.2/layer_profile_calculation_v2.2.py \
    --response ${studyDataDir}/layersim_experiment_hand_segmentation/sub-${subject_id}/smoothed_responses/${response}.nii.gz \
    --layers ${studyDataDir}/layersim_experiment_mri_vol2vol/sub-${subject_id}/rim_layers_equidist.nii \
    --columns ${studyDataDir}/layersim_experiment_hand_segmentation/sub-${subject_id}/rim_columns100.nii \
    --parcellation ${studyDataDir}/layersim_experiment_mri_vol2vol/sub-${subject_id}/aparc+aseg_transformed.nii"

## Run the Python script inside the container - Hand Segmentation Output
srun apptainer exec ${container} bash -c \
"source ${MINICONDA_PATH} && python ${studyDataDir}/layer_profile_calculation_v2.2/layer_profile_calculation_v2.2.py \
    --response ${studyDataDir}/layersim_experiment_hand_segmentation/sub-${subject_id}/smoothed_responses/${response}.nii.gz \
    --layers ${studyDataDir}/layersim_experiment_hand_segmentation/sub-${subject_id}/rim_layers_equidist.nii \
    --columns ${studyDataDir}/layersim_experiment_hand_segmentation/sub-${subject_id}/rim_columns100.nii \
    --parcellation ${studyDataDir}/layersim_experiment_mri_vol2vol/sub-${subject_id}/aparc+aseg_transformed.nii"

# Cleanup output logs into a separate directory
mkdir -p ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT
mv ${SLURM_SUBMIT_DIR}/*.err ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT/
mv ${SLURM_SUBMIT_DIR}/*.out ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT/

exit 0
