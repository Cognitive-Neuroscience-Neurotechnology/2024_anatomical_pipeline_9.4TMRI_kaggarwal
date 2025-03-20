#!/bin/bash -l

##############################
#       Job blueprint        #
##############################

#### define some basic SLURM properties for this job
#SBATCH --job-name=GLM
#SBATCH --output=GLM_%A_%a.out
#SBATCH --error=GLM_%A_%a.err
#SBATCH --partition=compute
#SBATCH --array=1-7
#SBATCH --time=1:00:00  
#SBATCH --mem=5GB  

# Define environment
container=/ptmp/kaggarwal/containers/mp2rage_recon-all_env-only.sif 
MINICONDA_PATH=/opt/conda/bin/activate 

# Define data directory
studyDataDir=/home/kaggarwal/ptmp/layersim_experiment

# Extract the responses from config file
config_file="config.txt"
subject_id=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$config_file")

echo "Processing subject: ${subject}"

## Run the Python script inside the container
srun apptainer exec ${container} bash -c \
"source ${MINICONDA_PATH} && python ${studyDataDir}/GLM/layerseg_linear_model.py \
    --manual_segmentation ${studyDataDir}/layersim_experiment_hand_segmentation/sub-${subject_id}/analysis_output_smooth/ \
    --pipeline_segmentation ${studyDataDir}/layersim_experiment_mri_vol2vol/sub-${subject_id}/analysis_output_smooth/"

# Cleanup output logs into a separate directory
mkdir -p ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT
mv ${SLURM_SUBMIT_DIR}/*.err ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT/
mv ${SLURM_SUBMIT_DIR}/*.out ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT/

exit 0

