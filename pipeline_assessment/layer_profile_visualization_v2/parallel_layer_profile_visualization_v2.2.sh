#!/bin/bash -l

##############################
#       Job blueprint        #
##############################

#### define some basic SLURM properties for this job
#SBATCH --job-name=layer_profile_visualization_v2.2
#SBATCH --output=layer_profile_visualization_v2.2_%A_%a.out
#SBATCH --error=layer_profile_visualization_v2.2_%A_%a.err
#SBATCH --partition=compute
#SBATCH --array=1-30
#SBATCH --time=1:00:00  
#SBATCH --mem=5GB  

# Define environment
container=/ptmp/kaggarwal/containers/mp2rage_recon-all_env-only.sif
MINICONDA_PATH=/opt/conda/bin/activate 

# Define data directory
studyDataDir=/home/kaggarwal/ptmp/layersim_experiment

# Extract the responses from config file
config_file="config.txt"
line=$(sed -n "$SLURM_ARRAY_TASK_ID"p "$config_file")
subject_id=$(echo "$line" | awk '{print $1}')
lobe=$(echo "$line" | awk '{print $2}')

echo "Processing subject: ${subject_id}"
echo "Processing response: ${lobe}"

## Run the Python script inside the container - Hand Segmentation Output
srun apptainer exec ${container} bash -c \
"source ${MINICONDA_PATH} && python ${studyDataDir}/layer_profile_visualization_v2.2/layer_profile_visualization_v2.2.py \
    --data_path ${studyDataDir}/layersim_experiment_hand_segmentation/sub-${subject_id}/analysis_output_v2_smooth/ \
    --lobe ${lobe}"

## Run the Python script inside the container - Pipeline Output
srun apptainer exec ${container} bash -c \
"source ${MINICONDA_PATH} && python ${studyDataDir}/layer_profile_visualization_v2.2/layer_profile_visualization_v2.2.py \
    --data_path ${studyDataDir}/layersim_experiment_mri_vol2vol/sub-${subject_id}/analysis_output_v2_smooth/ \
    --lobe ${lobe}"


# Cleanup output logs into a separate directory
mkdir -p ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT
mv ${SLURM_SUBMIT_DIR}/*.err ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT/
mv ${SLURM_SUBMIT_DIR}/*.out ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT/

exit 0