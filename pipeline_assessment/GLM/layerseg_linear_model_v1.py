## Plot GLM ##

import numpy as np
import os
import sys
import argparse
import matplotlib.pyplot as plt

def plot_glm(manual_path, pipeline_path):

    response_types = ['flat','deep_dec','deep_inc','middle_inc','middle_dec','superficial_dec','superficial_inc']
    lobes = ['frontal', 'parietal', 'temporal', 'occipital', 'brain']
    subject_ids = [46]   #[3, 9, 20, 29, 44, 46]
    transformation_matrices = {}

    for subject_id in subject_ids:
        print(f"\nProcessing subject: {subject_id}")

        # Update paths for each subject
        manual_segmentation = os.path.join(manual_path, f"sub-{subject_id}", "analysis_output_smooth")
        pipeline_segmentation = os.path.join(pipeline_path, f"sub-{subject_id}", "analysis_output_smooth")

        for lobe in lobes:
            gt_data = []
            op_data = []
        
            if lobe == 'brain':
                for response_type in response_types:

                    gt_data.append(np.loadtxt(os.path.join(manual_segmentation,
                                                                f'response_{response_type}',
                                                                f'mean_values_response_{response_type}_100columns.txt')))
                    op_data.append(np.loadtxt(os.path.join(pipeline_segmentation,
                                                                f'response_{response_type}',
                                                                f'mean_values_response_{response_type}_100columns.txt')))
            else:
                for response_type in response_types:
                    gt_data.append(np.loadtxt(os.path.join(manual_segmentation,
                                                            f'response_{response_type}',
                                                            f'{lobe}_data.txt')))
                    op_data.append(np.loadtxt(os.path.join(pipeline_segmentation,
                                                            f'response_{response_type}',
                                                            f'{lobe}_data.txt')))
        
            # Reshape data
            gt_data = np.array(gt_data).reshape(-1,3)
            op_data = np.array(op_data).reshape(-1,3)
            np.set_printoptions(threshold=np.inf)
            print("\nProcessing lobe: ", lobe)
            print("\nShape of gt_flat_data: ", np.shape(gt_data))
            print("Shape of op_flat_data: ", np.shape(op_data))

            # Assuming A and B are two lists of 700 (7 responses combined) 3-component vectors
            # A is a 700x3 matrix and B is a 700x3 matrix
            min_rows = min(gt_data.shape[0], op_data.shape[0])
            A = gt_data[:min_rows]
            B = op_data[:min_rows]

            # Create a mask to filter out rows with NaN values in either A or B
            mask = ~np.isnan(A).any(axis=1) & ~np.isnan(B).any(axis=1)

            # Apply the mask to filter out rows with NaN values
            A_filtered = A[mask]
            B_filtered = B[mask]
            print("Shape of A filtered (ground truth): ", np.shape(A_filtered)) # (700,3)
            print("Shape of B filtered (pipeline): ", np.shape(B_filtered))     # (700,3)

            # Solving using the equation: M = inv(A_T . A) . (A_T . B)
            M = np.linalg.inv(A_filtered.T @ A_filtered) @ A_filtered.T @ B_filtered
            print("\n Transformation Matrix M: \n", M)
            transformation_matrices[lobe] = M
    print("\n", transformation_matrices)


    # Plotting
    for lobe, M in transformation_matrices.items():
        # Create the plot
        plt.figure(figsize=(6, 6))
        plt.plot(['deep', 'middle', 'superficial'], M[0, :], label='deep', marker='o', color='blue')
        plt.plot(['deep', 'middle', 'superficial'], M[1, :], label='middle', marker='o', color='orange')
        plt.plot(['deep', 'middle', 'superficial'], M[2, :], label='superficial', marker='o', color='green')

        # Set plot labels, title, and legend
        plt.ylim(-0.1, 1.1)
        plt.title(f'{lobe} Transformation Matrix', fontsize=14)
        plt.xlabel('True Laminar Source of Signal', fontsize=12)
        plt.ylabel('Sampling Coefficients [a.u.]', fontsize=12)
        # plt.legend(title='Sampled Layer Signal', loc='upper center', bbox_to_anchor=(0.5, -0.1), fontsize=10)
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.2)
        
        # Save the plot to the output folder
        output_folder = os.path.join(pipeline_path, "transformation_matrix_plots")
        os.makedirs(output_folder, exist_ok=True)
        save_path = os.path.join(output_folder, f'{lobe}_transformation_matrix_sub-46.png')
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved {lobe} plot at {save_path}")



    # # Plotting GLM
    # fig, axes = plt.subplots(1, 5, figsize=(25, 5))
    # for i, (lobe, M) in enumerate(transformation_matrices.items()):
    #     ax = axes[i]
    #     # Plot each row of M as a line (representing each sampled layer signal)
    #     ax.plot(['deep', 'middle', 'superficial'], M[0, :], label='deep', marker='o', color='blue')
    #     ax.plot(['deep', 'middle', 'superficial'], M[1, :], label='middle', marker='o', color='orange')
    #     ax.plot(['deep', 'middle', 'superficial'], M[2, :], label='superficial', marker='o', color='green')
    #     # Set plot labels and title
    #     ax.set_title(f'{lobe}', fontsize=12)
    #     ax.set_xlabel('true laminar source of signal')
    #     ax.set_ylabel('sampling coefficients [a.u.]')
    #     ax.legend(title='sampled layer signal', loc='lower center', bbox_to_anchor=(0.5, -0.4), fontsize=10)
    # plt.tight_layout()
    # plt.subplots_adjust(bottom=0.25)
    # plt.savefig(os.path.join(pipeline_path, 'Transformation_matrix_coefficients.png'), dpi=600, bbox_inches='tight')
    # plt.show()
    # print("Plotting GLM Finished!!!!!")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Plot GLM")
    parser.add_argument("--manual_path", required = True, help = "Path to /home/kaggarwal/ptmp/layersim_experiment/layersim_experiment_hand_segmentation    ")
    parser.add_argument("--pipeline_path", required = True, help = "Path to /home/kaggarwal/ptmp/layersim_experiment/layersim_experiment_mri_vol2vol/synthstrip_results")
    
    args = parser.parse_args()
    
    plot_glm(args.manual_path, args.pipeline_path)
    












# # Extracting each layer for A and B
        # A_deep = A_filtered[:, 0].reshape(-1, 1)
        # B_deep = B_filtered[:, 0].reshape(-1, 1)
        # print("\n Shape of A_deep and B_deep: ", np.shape(A_deep), np.shape(B_deep))    #(700,1) 

        # A_middle = A_filtered[:, 1].reshape(-1, 1)
        # B_middle = B_filtered[:, 1].reshape(-1, 1)
        # print("Shape of A_middle and B_middle: ", np.shape(A_middle), np.shape(B_middle))    #(700,1) 

        # A_superficial = A_filtered[:, 2].reshape(-1, 1)
        # B_superficial = B_filtered[:, 2].reshape(-1, 1)
        # print("Shape of A_superficial and B_superficial: ", np.shape(A_superficial), np.shape(B_superficial))    #(700,1) 



        # # Solving M for each layer individually (Fitting A to B)
        # M_deep = np.linalg.inv(A_deep.T @ A_deep) @ (A_deep.T @ B_deep)
        # M_middle = np.linalg.inv(A_middle.T @ A_middle) @ (A_middle.T @ B_middle)
        # M_superficial = np.linalg.inv(A_superficial.T @ A_superficial) @ (A_superficial.T @ B_superficial)
        # M_A_to_B = np.array([M_superficial, M_middle, M_deep]).flatten()

        # print("\nTransformation Matrix M for deep layer (A to B): ", M_deep)
        # print("Transformation Matrix M for middle layer (A to B): ", M_middle)
        # print("Transformation Matrix M for superficial layer (A to B): ", M_superficial)
        # print("M_A_to_B: ", M_A_to_B)



        # # Solving M for each layer to the neighbouring layer (Fitting A to its own layers)
        # A_deep_superficial_average = ((np.array(A_deep) + np.array(A_superficial))/2)

        # M_A_deep = np.linalg.inv(A_deep.T @ A_deep) @ (A_deep.T @ A_middle)
        # M_A_middle = np.linalg.inv(A_middle.T @ A_middle) @ (A_middle.T @ A_deep_superficial_average )
        # M_A_superficial = np.linalg.inv(A_superficial.T @ A_superficial) @ (A_superficial.T @ A_middle)
        # M_A = np.array([M_A_superficial, M_A_middle, M_A_deep]).flatten()
        
        # print("\nTransformation Matrix M for deep layer to neighboring layer for Ground truth A: ", M_A_deep)
        # print("Transformation Matrix M for middle layer to neighboring layer for Ground truth A: ", M_A_middle)
        # print("Transformation Matrix M for superficial layer to neighboring layer for Ground truth A: ", M_A_superficial)



        # # Solving M for each layer to the neighbouring layer (Fitting B to its own layers)
        # B_deep_superficial_average = ((np.array(B_deep) + np.array(B_superficial))/2)

        # M_B_deep = np.linalg.inv(B_deep.T @ B_deep) @ (B_deep.T @ B_middle)
        # M_B_middle = np.linalg.inv(B_middle.T @ B_middle) @ (B_middle.T @ B_deep_superficial_average )
        # M_B_superficial = np.linalg.inv(B_superficial.T @ B_superficial) @ (B_superficial.T @ B_middle)
        # M_B = np.array([M_B_superficial, M_B_middle, M_B_deep]).flatten()
        
        # print("\nTransformation Matrix M for deep layer to neighboring layer for Pipeline B: ", M_B_deep)
        # print("Transformation Matrix M for middle layer to neighboring layer for Pipeline B: ", M_B_middle)
        # print("Transformation Matrix M for superficial layer to neighboring layer for Pipeline B: ", M_B_superficial)

        # # Store results for the lobe
        # lobe_data[lobe] = {
        #     'M_A_to_B': M_A_to_B,
        #     'M_A': M_A,
        #     'M_B': M_B
        # }






# def plot_lobe_layer_relationships(manual_segmentation, pipeline_segmentation):

#     print("\nFitting data for each lobe and layer!!!!!")
#     # Define response types and lobes
#     response_types = ['flat','deep_dec','deep_inc','middle_inc','middle_dec','superficial_dec','superficial_inc']
#     lobes = ['frontal', 'parietal', 'temporal', 'occipital']

#     # Create a figure for the 3x4 layout
#     fig, axes = plt.subplots(3, 4, figsize=(20, 15), sharex=True, sharey=True)

#     for col, lobe in enumerate(lobes):
#         gt_data_new = []
#         op_data_new = []
#         # Load lobe-specific data
#         for response_type in response_types:
#             gt_data_new.append(np.loadtxt(os.path.join(manual_segmentation, f'response_{response_type}', f'{lobe}_data.txt')))
#             op_data_new.append(np.loadtxt(os.path.join(pipeline_segmentation, f'response_{response_type}', f'{lobe}_data.txt')))

#         # Reshape data
#         gt_data_new = np.array(gt_data_new).reshape(-1, 3)
#         op_data_new = np.array(op_data_new).reshape(-1, 3)

#         # Create a mask to filter out rows with NaN values in either A or B
#         mask = ~np.isnan(gt_data_new).any(axis=1) & ~np.isnan(op_data_new).any(axis=1)

#         # Apply the mask to filter out rows with NaN values
#         A_filtered = gt_data_new[mask]
#         B_filtered = op_data_new[mask]

#         # Extract individual layers for A and B
#         A_deep = A_filtered[:, 0].reshape(-1, 1)
#         B_deep = B_filtered[:, 0].reshape(-1, 1)
#         A_middle = A_filtered[:, 1].reshape(-1, 1)
#         B_middle = B_filtered[:, 1].reshape(-1, 1)
#         A_superficial = A_filtered[:, 2].reshape(-1, 1)
#         B_superficial = B_filtered[:, 2].reshape(-1, 1)

#         # Calculate transformation matrices
#         M_deep = np.linalg.inv(A_deep.T @ A_deep) @ (A_deep.T @ B_deep)
#         M_middle = np.linalg.inv(A_middle.T @ A_middle) @ (A_middle.T @ B_middle)
#         M_superficial = np.linalg.inv(A_superficial.T @ A_superficial) @ (A_superficial.T @ B_superficial)

#         # Plot for each layer
#         for row, (A, B, M, layer) in enumerate([(A_superficial, B_superficial, M_superficial, 'superficial'),
#                                                  (A_middle, B_middle, M_middle, 'middle'),
#                                                  (A_deep, B_deep, M_deep, 'deep')]):

#             ax = axes[row, col]
#             ax.plot(A, B, 'o', markersize=5, label=f'{lobe.capitalize()} {layer}')
#             ax.plot(A, M * A, 'r', label='Fitted Line')
#             ax.set_title(f'{lobe.capitalize()} {layer}')
#             ax.set_xlabel('Ground Truth (A)')
#             ax.set_ylabel('Pipeline (B)')
#             ax.grid(True, linestyle='--', alpha=0.6)
#             ax.legend()

#     # Adjust layout and save
#     plt.tight_layout()
#     plt.savefig(os.path.join(pipeline_segmentation, 'Lobe_Layer_Relationships.png'), dpi=600, bbox_inches='tight')
#     plt.show()
#     print("\nFitting data for each lobe and layer finished!!!!!")


    # # Solve for the transformation matrix M using the filtered arrays
    # M1, a, b, c = np.linalg.lstsq(A_filtered, B_filtered, rcond=None)
    # print("\n Transformation Matrix M using least-squares method: \n", M1)
    # print("\n a: ", a)
    # print("\n b: ", b)
    # print("\n c: ", c)