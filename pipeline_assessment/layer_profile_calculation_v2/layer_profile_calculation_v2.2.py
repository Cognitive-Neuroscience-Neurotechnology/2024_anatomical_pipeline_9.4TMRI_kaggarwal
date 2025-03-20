### Layer Profile Calculation v2.2 ###
## Update: simulating responses and smoothing columns individually ##
## Mapping each column to a specific parcel and then combining parcels into lobes ##
## Calculating the mean values for each column and grouping them together lobe wise ##

import sys
from tqdm import tqdm
import subprocess
import numpy as np
import nibabel as nib
import os
import argparse
from collections import defaultdict

# Create a binary mask for a specific column using fslmaths
def create_roi(column, columns_file, response_file, subject_id, intermediate_files_path):

    response_name = os.path.splitext(os.path.splitext(os.path.basename(response_file))[0])[0]
    output_file = os.path.join(intermediate_files_path, f"{subject_id}_{response_name}_sim_roi_mask_{column}.nii.gz")
    command = f"fslmaths {columns_file} -thr {column} -uthr {column} -bin {output_file}"
    subprocess.run(command, shell=True, check=True)

    return output_file

def create_roi_response(column, sim_roi, response_file, subject_id, intermediate_files_path):

    response_name = os.path.splitext(os.path.splitext(os.path.basename(response_file))[0])[0]
    output_file = os.path.join(intermediate_files_path, f"{subject_id}_{response_name}_roi_response_{column}.nii.gz")
    command = f"fslmaths {response_file} -mas {sim_roi} {output_file}"
    subprocess.run(command, shell=True, check=True)

    return output_file

def smooth_roi_response(column, response_file, roi_response, subject_id, intermediate_files_path):
    
    response_name = os.path.splitext(os.path.splitext(os.path.basename(response_file))[0])[0]
    output_file = os.path.join(intermediate_files_path, f"{subject_id}_{response_name}_roi_response_smoothed_{column}.nii.gz")
    command = f"fslmaths {roi_response} -s 0.42553 {output_file}"
    subprocess.run(command, shell=True, check=True)

    return output_file

def create_roi_response_mask(column, response_file, roi_response_smoothed, subject_id, intermediate_files_path):
    response_name = os.path.splitext(os.path.splitext(os.path.basename(response_file))[0])[0]
    output_file = os.path.join(intermediate_files_path, f"{subject_id}_{response_name}_roi_response_mask_{column}.nii.gz")
    command = f"fslmaths {roi_response_smoothed} -thr 0 -bin {output_file}"
    subprocess.run(command, shell=True, check=True)

    return output_file

# Process a single column using LN2_PROFILE function
def process_column(column, response_file, layer_file, columns_file, subject_id):

    # Make file path for saving temporary files
    cwd = os.path.dirname(os.path.abspath(layer_file))
    response_name = os.path.splitext(os.path.splitext(os.path.basename(response_file))[0])[0]
    intermediate_files_path = os.path.join(cwd, 'analysis_output_v2_smooth', response_name, 'intermediate_files')
    os.makedirs(intermediate_files_path, exist_ok=True)

    # Create binary simulation ROI column mask
    sim_roi = create_roi(column, columns_file, response_file, subject_id, intermediate_files_path)

    # Generate a response localized to simulation roi
    roi_response = create_roi_response(column, sim_roi, response_file, subject_id, intermediate_files_path)

    # Smooth the ROI response
    roi_response_smoothed = smooth_roi_response(column, response_file, roi_response, subject_id, intermediate_files_path)

    # Create ROI response mask
    roi_response_mask = create_roi_response_mask(column, response_file, roi_response_smoothed, subject_id, intermediate_files_path)

    # Run LN2_PROFILE function to get mean values for the column ROI
    output_file = f"layer_profile_{subject_id}_{response_name}_col_{column}.txt"
    command = f"LN2_PROFILE -input {roi_response} -layers {layer_file} -mask {roi_response_mask} -output {output_file}"
    subprocess.run(command, shell=True, check=True)
    
    # Read and return the data
    data = np.loadtxt(output_file)
    
    # Remove temporary files
    os.remove(output_file)
    
    return data


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



def map_columns_to_parcels(rim_columns_file, parcellation_file):
    rim_columns = nib.load(rim_columns_file).get_fdata()
    parcellation = nib.load(parcellation_file).get_fdata().astype(int)
    
    print("\n Mapping columns to parcels... \n")
    column_to_parcel = {}
    parcel_info = {}
    for column in tqdm(range(1, int(np.max(rim_columns)) + 1), desc="Mapping columns to parcels"):
        column_mask = rim_columns == column
        if np.any(column_mask):
            print("Shape of parcellation file: ", np.shape(parcellation))   # (256, 256, 192)
            print("Shape of Column mask: ", np.shape(column_mask))  # (256, 256, 192)
            
            parcel_values = parcellation[column_mask]
            print("\n Parcel values - which parcel does each voxel belong to: ", (parcel_values))  # [1029 1029 1029 ...    0 1011 1011]
            parcel_values = parcel_values[parcel_values > 0]    # remove background voxels
            print("\n Removed voxels belonging to background: ", (parcel_values))  # [1029 1029 1029 ... 1011 1011 1011]
            print("\n Length of Parcel values - total number of voxels in that column: ", len(parcel_values))   # 8466 voxels
            
            if len(parcel_values) > 0:
                voxel_count = np.bincount(parcel_values)
                print("\n Voxel count - frequency of each parcel: ", voxel_count)   # [   0    0  184 ...    0    0 1877]
                most_common_parcel = np.argmax(voxel_count)
                print("\n Most common parcel - Pick parcel with most voxels: ", most_common_parcel) # 1008
                print("\n Number of voxels belonging to the chosen parcel: ", voxel_count[most_common_parcel], "\n")  # 5656 voxels
                column_to_parcel[column] = most_common_parcel
                parcel_info[column] = (len(parcel_values), voxel_count[most_common_parcel])
            else:
                column_to_parcel[column] = 0  
                parcel_info[column] = (0, 0)

    print(f"\n Mapped {len(column_to_parcel)} columns to parcels. \n")
    print(f"{'Column':<10}{'Parcel':<10}{'Total_voxels_#':<20}{'Chosen_voxels_#':<20}")
    for column, parcel in column_to_parcel.items():
        parcel_len, voxel_count = parcel_info[column]
        print(f"{column:<10}{parcel:<10}{parcel_len:<20}{voxel_count:<20}")

    return column_to_parcel


# Dictionary for mapping parcel numbers to lobes
lobe_mapping = {
'Frontal': [1003, 1012, 1014, 1017, 1018, 1019, 1020, 1024, 1027, 1028, 1032,
            2003, 2012, 2014, 2017, 2018, 2019, 2020, 2024, 2027, 2028, 2032],
'Parietal': [1008, 1022, 1023, 1025, 1029, 1031,
             2008, 2022, 2023, 2025, 2029, 2031],
'Temporal': [1001, 1006, 1007, 1009, 1015, 1016, 1030, 1033, 1034,
             2001, 2006, 2007, 2009, 2015, 2016, 2030, 2033, 2034],
'Occipital': [1005, 1011, 1013, 1021,
              2005, 2011, 2013, 2021],
}


# Get the lobe for a given parcel
def get_lobe(parcel):
    for lobe, parcels in lobe_mapping.items():
        if parcel in parcels:
            return lobe
    return "Unknown"


## Aggregate all columns
def aggregate_columns(response_file, layer_file, columns_file, parcellation_file):

    # Map column to parcel
    column_to_parcel = map_columns_to_parcels(columns_file, parcellation_file)
    
    # Extract the number of columns from the rim_columns filename
    total_columns = int(columns_file.split('columns')[-1].split('.')[0])

    # Initialize expected layers and arrays for storing each column data
    expected_layers = 3
    mean_values = np.zeros((total_columns, expected_layers))
    subject_id = os.path.basename(os.path.dirname(os.path.dirname(response_file)))

    # Make dictionaries for parcels data and lobe data
    parcel_data = defaultdict(list)
    lobe_data = defaultdict(list)
    
    # Loop through each column
    for column in range(1, total_columns + 1):
        # Process each column using LN2_PROFILE function
        column_data = process_column(column, response_file, layer_file, columns_file, subject_id)

        # Check shape of column and pad it if required
        print('Shape of Column: ', column_data.shape)
        column_data = pad_column_data(column_data, expected_layers)

        # Store mean values for this column
        mean_values[column-1] = column_data[:, 1]

        # Store mean values of parcels
        parcel = column_to_parcel[column]
        parcel_data[parcel].append(column_data[:, 1])
        print(f"Stored mean value for the column {column} in parcel {parcel}")

    # Populate lobe_data
    for parcel, data in parcel_data.items():
        lobe = get_lobe(parcel)
        lobe_data[lobe].extend(data)
    
    # Print summary of parcel data
    print("\nParcel Data Summary:")
    for parcel in sorted(parcel_data.keys()):
        data = parcel_data[parcel]
        print(f"Parcel {parcel}: {len(data)} columns")
        print(f"  First column data: {data[0]}")
        print(f"  Last column data: {data[-1]}")
        print()
    

    # Save mean values for all columns
    cwd = os.path.dirname(os.path.abspath(layer_file))
    response_name = os.path.splitext(os.path.splitext(os.path.basename(response_file))[0])[0]
    mean_values_file = f'mean_values_{response_name}_{total_columns}columns.txt'
    os.makedirs(os.path.join(cwd, 'analysis_output_v2_smooth', response_name), exist_ok=True)
    np.savetxt(os.path.join(cwd, 'analysis_output_v2_smooth', response_name, mean_values_file), mean_values, fmt='%.6f') 
    print(f"Mean values for all columns saved!!!!!!!!")

    # Save data for each lobe to a separate file
    for lobe, data in lobe_data.items():
        filename = os.path.join(cwd, 'analysis_output_v2_smooth', response_name, f"{lobe.lower().replace(' ', '_')}_data.txt")
        with open(filename, 'w') as f:
            for row in data:
                f.write(f"{row[0]:.6f} {row[1]:.6f} {row[2]:.6f}\n")
    print("Files have been created for each lobe.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Aggregate layer profiles across columns.")
    parser.add_argument("--response", required = True, help = "Path to response file from Manual segmentation")
    parser.add_argument("--layers", required = True, help = "Path to the rim_layer_equidist.nii file")
    parser.add_argument("--columns", required = True, help = "Path to the rim columns file - 100, 1000, 10000")
    parser.add_argument("--parcellation", required=True, help="Path to the aparc+aseg.nii.gz file from FreeSurfer")

    args = parser.parse_args()
    
    aggregate_columns(args.response, args.layers, args.columns, args.parcellation)