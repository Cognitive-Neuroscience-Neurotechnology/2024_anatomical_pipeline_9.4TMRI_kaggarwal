#!/bin/bash -l

##############################
#       Job blueprint        #
##############################

#### define some basic SLURM properties for this job
#SBATCH --job-name=layer_profile_calculation_v3.2
#SBATCH --output=layer_profile_calculation_v3.2_%A_%a.out
#SBATCH --error=layer_profile_calculation_v3.2_%A_%a.err
#SBATCH --partition=compute
#SBATCH --array=1-18
#SBATCH --time=1:00:00  
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

## Run the Python script inside the container
srun apptainer exec ${container} bash -c \
"source ${MINICONDA_PATH} && python ${studyDataDir}/layer_profile_calculation_v3/layer_profile_calculation_v3.py \
    --flat_response_manual ${studyDataDir}/layersim_experiment_hand_segmentation/sub-${subject_id}/smoothed_responses/response_flat.nii.gz \
    --changed_response_manual ${studyDataDir}/layersim_experiment_hand_segmentation/sub-${subject_id}/smoothed_responses/${response}.nii.gz \
    --layers_manual ${studyDataDir}/layersim_experiment_hand_segmentation/sub-${subject_id}/rim_layers_equidist.nii \
    --layers_pipeline ${studyDataDir}/layersim_experiment_mri_vol2vol/sub-${subject_id}/rim_layers_equidist.nii \
    --columns_manual ${studyDataDir}/layersim_experiment_hand_segmentation/sub-${subject_id}/rim_columns100.nii \
    --columns_pipeline ${studyDataDir}/layersim_experiment_hand_segmentation/sub-${subject_id}/rim_columns100.nii"
# Note: Columns are coming from hand segmentation. No columns will come from pipeline


# Cleanup output logs into a separate directory
mkdir -p ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT
mv ${SLURM_SUBMIT_DIR}/*.err ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT/
mv ${SLURM_SUBMIT_DIR}/*.out ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT/

exit 0

