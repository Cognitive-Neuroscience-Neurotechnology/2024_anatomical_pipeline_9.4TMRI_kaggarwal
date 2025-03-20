#!/bin/bash -l

##############################
#       Job blueprint        #
##############################

#### define some basic SLURM properties for this job
#SBATCH --job-name=layer_simulation_v1
#SBATCH --output=layer_simulation_v1_%A_%a.out
#SBATCH --error=layer_simulation_v1_%A_%a.err
#SBATCH --partition=compute
#SBATCH --array=1-6
#SBATCH --time=4:00:00  
#SBATCH --mem=5GB

# Define environment
container=/ptmp/kaggarwal/containers/gfae.sif 
MINICONDA_PATH=/opt/conda/bin/activate 

# Define data directory
studyDataDir=/home/kaggarwal/ptmp/layersim_experiment

# Extract the subject ID from config file
config_file="config_layer_simulation_v1.txt"
subject_id=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$config_file")

# Define segmentation file path
# segmentation_file="${studyDataDir}/layersim_experiment_hand_segmentation/sub-${subject_id}/sub-${subject_id}_ses-1_manual_seg.nii"
segmentation_file="${studyDataDir}/layersim_experiment_mri_vol2vol/synthstrip_results/sub-${subject_id}/sub-${subject_id}_ses-1_seg_mri_vol2vol_transformed.nii"

echo "Processing subject ${subject_id}"

# Run the processing script inside the container
srun apptainer exec ${container} bash -c "source ${MINICONDA_PATH} && bash ${studyDataDir}/layer_simulation/layer_simulation_v1.sh ${subject_id}"

# Cleanup output logs into a separate directory
mkdir -p ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT
mv ${SLURM_SUBMIT_DIR}/*.err ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT/
mv ${SLURM_SUBMIT_DIR}/*.out ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT/

exit 0

