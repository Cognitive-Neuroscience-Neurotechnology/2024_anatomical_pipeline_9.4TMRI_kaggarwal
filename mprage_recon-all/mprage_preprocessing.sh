#!/bin/bash -l
 
##############################
#       Job blueprint        #
##############################


#### define some basic SLURM properties for this job - there can be many more!
#SBATCH --job-name=mprage_preprocessing
#SBATCH --output=mprage_preprocessing_job_%A_%a.out
#SBATCH --error=mprage_preprocessing_job_%A_%a.err
#SBATCH --partition compute
#SBATCH --exclusive=user
#SBATCH --array=1-2 #as many lines as in config file (need to be exact line names)
#SBATCH --time=12:00:00 

# How much memory you need.
# --mem will define memory per node and
# --mem-per-cpu will define memory per CPU/core. Choose one of those.
##SBATCH --mem-per-cpu=1M
##SBATCH --mem=5GB    # this one is not in effect, due to the double hash
 
# Turn on mail notification. There are many possible self-explaining values:
# NONE, BEGIN, END, FAIL, ALL (including all aforementioned)
# For more values, check "man sbatch"
#SBATCH --mail-type=BEGIN,FAIL,TIME_LIMIT
#SBATCH --mail-user=kunal.aggarwal@tuebingen.mpg.de  

# You may not place any commands before the last SBATCH directive
 
#### Do the actual work:

# Define environment
container=/ptmp/kaggarwal/containers/mp2rage_recon-all_env-only.sif
MINICONDA_PATH=/opt/conda/bin/activate
#pythonenv_path=/home/rlorenz/python_envs/retrocue_env

# Define some variables
studyDataDir=/ptmp/kaggarwal/BIDS_data/2024_9T_AnatomicalPipeline/Ultracortex_v1.1.0

# Read subject and session from config file
config_file="config.txt"
total_lines=$(wc -l < "$config_file") # Count the number of lines in the config file
line=$(sed -n "$SLURM_ARRAY_TASK_ID"p "$config_file")
subject=$(echo "$line" | awk '{print $1}')
session=$(echo "$line" | awk '{print $2}')

echo ${subject}
echo ses-${session}

# Then use it to run bash out of the singularity container 
srun apptainer exec ${container} bash -c "source ${MINICONDA_PATH} && python ${SLURM_SUBMIT_DIR}/mprage_recon-all.py --mprage ${studyDataDir}/${subject}/ses-${session}/anat/${subject}_ses-${session}_T1w.nii --skull-strip synthstrip"

# After the job is done we copy our output back to $SLURM_SUBMIT_DIR
mkdir -p ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT
#rm ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT/*
mv ${SLURM_SUBMIT_DIR}/*.err ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT/
mv ${SLURM_SUBMIT_DIR}/*.out ${SLURM_SUBMIT_DIR}/SLURM_OUTPUT/
 
# Finish the script
exit 0