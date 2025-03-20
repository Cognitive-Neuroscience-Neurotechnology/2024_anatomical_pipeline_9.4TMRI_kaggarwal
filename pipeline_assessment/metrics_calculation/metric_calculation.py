## Dice coefficient calculation between rim_columns100.nii in manual and pipeline output

import argparse
import time
import nibabel as nib
import numpy as np
from scipy.spatial.distance import directed_hausdorff


def calculate_dice_coefficient(manual_foreground, pipeline_foreground):
    # Calculate the intersection and union of the foreground masks
    intersection = np.sum(manual_foreground * pipeline_foreground)
    print("\n intersection: ", intersection)
    union = np.sum(manual_foreground) + np.sum(pipeline_foreground)
    print("\n union: ", union)
    dice_coefficient = (2 * intersection) / union
    print(f"\n Dice coefficient: {dice_coefficient:.2f}")
    
    return dice_coefficient


def calculate_hausdorff_distance(manual_coords, pipeline_coords, voxel_sizes):
    # Scale coordinates to millimeters
    manual_coords_mm = manual_coords * voxel_sizes
    pipeline_coords_mm = pipeline_coords * voxel_sizes

    # Compute the directed Hausdorff distances
    print("\n Calculating hausdorff distance in mm ....")
    hausdorff_distance_1 = directed_hausdorff(manual_coords_mm, pipeline_coords_mm)[0]
    hausdorff_distance_2 = directed_hausdorff(pipeline_coords_mm, manual_coords_mm)[0]
    print("\n hausdorff distance 1: ", hausdorff_distance_1)
    print("\n hausdorff distance 2: ", hausdorff_distance_2)

    # Take the maximum of the two directed distances
    hausdorff_distance = max(hausdorff_distance_1, hausdorff_distance_2)

    return hausdorff_distance


def metric_calculation(manual_path, pipeline_path):
    # Load the manual and pipeline NIfTI files
    manual_nii = nib.load(manual_path)
    pipeline_nii = nib.load(pipeline_path)

    # Extract data from NIfTI files
    manual_data = manual_nii.get_fdata()
    pipeline_data = pipeline_nii.get_fdata()

    # Extract voxel resolution from Affine matrix
    print("\n Affine matrix: ", manual_nii.affine)
    voxel_sizes = np.sqrt((manual_nii.affine[:3, :3] ** 2).sum(axis=0))
    print("\n Voxel sizes (in mm):", voxel_sizes)

    # Selcting only GM (3) - WM(2), CSF(1), Background(0) for pipeline output
    # For manual segmentation, choosing 3 for left and 42 for right GM
    manual_foreground = (manual_data == 3) | (manual_data == 42)
    pipeline_foreground = pipeline_data > 2

    # Extract the coordinates of the foreground voxels
    manual_coords = np.argwhere(manual_foreground)
    pipeline_coords = np.argwhere(pipeline_foreground)
    print("\n shape of manual_coords: ", np.shape(manual_coords))
    print("shape of pipeline_coords: ", np.shape(pipeline_coords))
    print("First few manual_coords:", manual_coords[:5])
    print("First few pipeline_coords:", pipeline_coords[:5])

    # Compute the Dice coefficient
    dice_coefficient = calculate_dice_coefficient(manual_foreground, pipeline_foreground)

    # Compute the Hausdorff Coefficient
    hausdorff_distance = calculate_hausdorff_distance(manual_coords, pipeline_coords, voxel_sizes)
    print(f"\n Hausdorff distance: {hausdorff_distance:.2f}")

    return dice_coefficient, hausdorff_distance


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Dice coefficient calculation between manual segmentation and rim.nii file")
    parser.add_argument("--manual", required = True, help = "Path to layersim_experiment_hand_segmentation/sub-id/manual_seg.nii/")
    parser.add_argument("--pipeline", required = True, help = "Path to layersim_experiment_mri_vol2vol/sub-id/rim.nii.gz/")

    args = parser.parse_args()

    metric_calculation(args.manual, args.pipeline)