### Layer Profile Calculation v3 ###
## Update: Using new method of columnwise response formation and making masks
## Creating new NIFTI file with response contrast for each layer ##
## Response contrast = Pipeline(change - flat) / Manual(change - flat) ##

import sys
from tqdm import tqdm
import subprocess
import numpy as np
import nibabel as nib
import os
import argparse
import uuid

# Create a binary mask for a specific column using fslmaths
def create_roi(column, columns_file, response_file, subject_id, unique_id, intermediate_files_path):

    response_name = os.path.splitext(os.path.splitext(os.path.basename(response_file))[0])[0]
    output_file = os.path.join(intermediate_files_path, f"{subject_id}_{response_name}_sim_roi_mask_{column}_{unique_id}.nii.gz")
    command = f"fslmaths {columns_file} -thr {column} -uthr {column} -bin {output_file} -odt int"
    subprocess.run(command, shell=True, check=True)

    return output_file

def create_roi_response(column, sim_roi, response_file, subject_id, unique_id, intermediate_files_path):

    response_name = os.path.splitext(os.path.splitext(os.path.basename(response_file))[0])[0]
    output_file = os.path.join(intermediate_files_path, f"{subject_id}_{response_name}_roi_response_{column}_{unique_id}.nii.gz")
    command = f"fslmaths {response_file} -mas {sim_roi} {output_file}"
    subprocess.run(command, shell=True, check=True)

    return output_file

def smooth_roi_response(column, response_file, roi_response, subject_id, unique_id, intermediate_files_path):
    
    response_name = os.path.splitext(os.path.splitext(os.path.basename(response_file))[0])[0]
    output_file = os.path.join(intermediate_files_path, f"{subject_id}_{response_name}_roi_response_smoothed_{column}_{unique_id}.nii.gz")
    command = f"fslmaths {roi_response} -s 0.42553 {output_file}"
    subprocess.run(command, shell=True, check=True)

    return output_file

def create_roi_response_mask(column, response_file, roi_response_smoothed, subject_id, unique_id, intermediate_files_path):
    response_name = os.path.splitext(os.path.splitext(os.path.basename(response_file))[0])[0]
    output_file = os.path.join(intermediate_files_path, f"{subject_id}_{response_name}_roi_response_mask_{column}_{unique_id}.nii.gz")
    command = f"fslmaths {roi_response_smoothed} -thr 0 -bin {output_file}"
    subprocess.run(command, shell=True, check=True)

    return output_file


# Process a single column using LN2_PROFILE function to give mean, std and no. of voxels 
def process_column(column, response_file, layer_file, columns_file, subject_id):

    # Make file path for saving temporary files
    cwd = os.path.dirname(os.path.abspath(layer_file))
    response_name = os.path.splitext(os.path.splitext(os.path.basename(response_file))[0])[0]
    intermediate_files_path = os.path.join(cwd, 'analysis_output_v2_smooth', response_name, 'intermediate_files')
    os.makedirs(intermediate_files_path, exist_ok=True)

    # Create binary simulation ROI column mask
    unique_id = str(uuid.uuid4())[:8]   # for parallely running subjects
    sim_roi = create_roi(column, columns_file, response_file, subject_id, unique_id, intermediate_files_path)

    # Generate a response localized to simulation roi
    roi_response = create_roi_response(column, sim_roi, response_file, subject_id, unique_id, intermediate_files_path)

    # Smooth the ROI response
    roi_response_smoothed = smooth_roi_response(column, response_file, roi_response, subject_id, unique_id, intermediate_files_path)

    # Create ROI response mask
    roi_response_mask = create_roi_response_mask(column, response_file, roi_response_smoothed, subject_id, unique_id, intermediate_files_path)
    
    # Run LN2_PROFILE function to get mean values for the column ROI
    output_file = f"layer_profile_{subject_id}_{response_name}_col_{column}_{unique_id}.txt"
    command = f"LN2_PROFILE -input {roi_response} -layers {layer_file} -mask {roi_response_mask} -output {output_file}"
    subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL)
    
    # Read and return the data
    data = np.loadtxt(output_file)
    
    # Remove temporary files
    os.remove(output_file)

    # Check shape of column and pad it if required
    # print('Shape of Column: ', data.shape)
    data = pad_column_data(data)
    # print('\nShape of Column after padding: ', data.shape)
    
    return data


# # Pad the column data with zeros if it has fewer than the expected number of layers
# def pad_column_data(column_data, expected_layers = 3):

#     current_layers = column_data.shape[0]
#     if current_layers < expected_layers:
#         padding = np.full((expected_layers - current_layers, column_data.shape[1]), np.nan)
#         return np.vstack((column_data, padding))
    
#     return column_data

# # Pad the column data with zeros if it has fewer than the expected number of layers
def pad_column_data(column_data, expected_layers=3):
    if column_data.size == 0:
        return np.full((expected_layers, 4), np.nan)
    
    current_layers = column_data.shape[0]
    
    if column_data.ndim == 1:
        column_data = column_data[:, np.newaxis]
    
    if current_layers < expected_layers:
        padding = np.full((expected_layers - current_layers, column_data.shape[1]), np.nan)
        return np.vstack((column_data, padding))
    
    return column_data


# Normalize the final output
def normalize_data(input_data):

    data_min, data_max = input_data.min(), input_data.max()
    normalized_data = (input_data - data_min) / (data_max - data_min)

    return normalized_data


# Update the output data array with new values for the current column
def update_nifti_with_column_values(column, new_column_data, columns_manual, selected_layer, output_image, response_values):

    # Load the rim columns file and create an empty array of same size
    rim_img = nib.load(columns_manual)
    rim_data = rim_img.get_fdata()
    
    # Select the layer number based on layer name
    if selected_layer == "deep":
        layer_number = 0
    elif selected_layer == "middle":
        layer_number = 1
    elif selected_layer == "superficial":
        layer_number = 2

    # Create a mask and allocate new value to the whole column
    column_mask = (rim_data == column)
    output_image[column_mask] = new_column_data[layer_number, 1]    # new_column_data is 3x4. Using column 1 for mean values

    # Create dictionary with all column values
    response_values[column] = new_column_data[layer_number, 1]
    
    return output_image, response_values


## Transform all columns
def transform_columns(flat_response_manual, changed_response_manual,
                    layers_manual, layers_pipeline, 
                    columns_manual, columns_pipeline):

    # Load a reference NIfTI to get dimensions and header info
    ref_img = nib.load(flat_response_manual)
    output_image = np.zeros_like(ref_img.get_fdata())
    
    # Extract number of columns from columns filename and create dictionary for storing new values
    total_columns = int(columns_manual.split('columns')[-1].split('.')[0])
    response_values = {}
    subject_id = os.path.basename(os.path.dirname(os.path.dirname(flat_response_manual)))

    # Selecting the layer name for allocating new values
    selected_layer = os.path.basename(changed_response_manual).split('_')[1]
    print("\nSelected layer: ",selected_layer,"\n")
    
    # Loop through each column
    for column in range(1, total_columns + 1):   
        
        # Process each column using LN2_PROFILE function to get mean, std, and no. of voxels for the column
        column_data_flat_manual = process_column(column, flat_response_manual, layers_manual, columns_manual, subject_id)
        column_data_changed_manual = process_column(column, changed_response_manual, layers_manual, columns_manual, subject_id)
        column_data_flat_pipeline = process_column(column, flat_response_manual, layers_pipeline, columns_manual, subject_id)
        column_data_changed_pipeline = process_column(column, changed_response_manual, layers_pipeline, columns_manual, subject_id)

        change_in_pipeline = column_data_changed_pipeline - column_data_flat_pipeline
        change_in_manual = column_data_changed_manual - column_data_flat_manual
        
        new_column_data = (np.nan_to_num( (change_in_pipeline) / (change_in_manual) )) # removed abs
    
        if column == 13:
            np.set_printoptions(threshold=sys.maxsize)
            print("\ncolumn_data_changed_pipeline: \n", column_data_changed_pipeline)
            print("\ncolumn_data_flat_pipeline: \n", column_data_flat_pipeline)
            print("\ncolumn_data_changed_manual: \n", column_data_changed_manual)
            print("\ncolumn_data_flat_manual: \n", column_data_flat_manual)
            print("\nDifference_pipeline: \n", change_in_pipeline)
            print("\nDifference_manual: \n", change_in_manual)
            print("\nnew_column_data: \n", new_column_data)

        # Update output data with new values for this column
        output_image, response_values = update_nifti_with_column_values(column, new_column_data, columns_manual, 
                                                       selected_layer, output_image, response_values)
        print(f"\nProcessed column {column}/{total_columns}")

    print("\nMax value of new output file: ", np.max(output_image), "\n")
    print("\nMin value of new output file: ", np.min(output_image), "\n")
    print("\nAll values of new output file: ")
    for value in response_values.values():
        print(value)

    # Save the output NIfTI
    layer_name = '_'.join(os.path.basename(changed_response_manual).split('_')[1:3]).replace('.nii', '')
    os.makedirs(os.path.join(os.path.dirname(layers_pipeline), 'differential_transformations_v2'), exist_ok=True)
    output_file = os.path.join(os.path.dirname(layers_pipeline), "differential_transformations_v2", f'transformed_response_{layer_name}.nii.gz')
    response_img = nib.load(changed_response_manual)
    output_img = nib.Nifti1Image(output_image, response_img.affine, response_img.header)
    nib.save(output_img, output_file)
    print(f"\nSaved transformed data to: {output_file}")
    
    return output_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Transform layer profiles across columns.")
    parser.add_argument("--flat_response_manual", required = True, help = "Path to flat response file from Manual segmentation")
    parser.add_argument("--changed_response_manual", required = True, help = "Path to changed response file from Manual segmentation")
    parser.add_argument("--layers_manual", required = True, help = "Path to the rim_layer_equidist.nii file from manual segmentation")
    parser.add_argument("--layers_pipeline", required = True, help = "Path to the rim_layer_equidist.nii file from Pipeline segmentation")
    parser.add_argument("--columns_manual", required = True, help = "Path to the rim columns file - 100, 1000, 10000 from Manual segmentation")
    parser.add_argument("--columns_pipeline", required = True, help = "Path to the rim columns file - 100, 1000, 10000 from Pipeline segmentation")

    args = parser.parse_args()
    
    transform_columns(args.flat_response_manual, args.changed_response_manual,
                    args.layers_manual, args.layers_pipeline,
                    args.columns_manual, args.columns_pipeline)
