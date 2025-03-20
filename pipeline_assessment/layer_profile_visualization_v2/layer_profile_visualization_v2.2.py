## Create violin plots for multiple responses and then combines them together   

import numpy as np
import matplotlib.pyplot as plt
import argparse
import os

def set_publication_style():
    plt.style.use('default')
    plt.rcParams.update({
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'axes.edgecolor': 'black',
        'axes.linewidth': 1.5,
        'axes.grid': True,
        'grid.color': '#CCCCCC',
        'grid.linestyle': ':',
        'font.family': 'Arial',
        'font.size': 12,
        'xtick.major.size': 6,
        'xtick.major.width': 1.5,
        'ytick.major.size': 6,
        'ytick.major.width': 1.5,
    })

def plot_layer_profile(ax, data, title, highlight_layer=None):
    layer_names = ['Superficial', 'Middle', 'Deep']
    default_color = '#555555'
    highlight_color = '#4FADFF'
    colors = [default_color] * 3
    if highlight_layer in layer_names:
        colors[layer_names.index(highlight_layer)] = highlight_color

    plot_data = []
    means = []
    for i in range(3):
        valid_data = data[(~np.isnan(data[:, 2-i])) & (data[:, 2-i] > 0.1), 2-i]
        plot_data.append(valid_data)
        means.append(np.mean(valid_data))

    parts = ax.violinplot(plot_data, showmeans=False, showmedians=False, showextrema=False)
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_edgecolor('black')
        pc.set_alpha(0.7)
        pc.set_linewidth(1.5)

    box_parts = ax.boxplot(plot_data, positions=[1, 2, 3], widths=0.2, 
                           patch_artist=False, showfliers=False, zorder=3)
    
    for element in ['boxes', 'whiskers', 'means', 'medians', 'caps']:
        plt.setp(box_parts[element], color='black', linewidth=1.5)

    ax.plot([1, 2, 3], means, color='red', linestyle='-', linewidth=2, marker='o', markersize=8)

    ax.set_xlabel('Layer', fontsize=14, fontweight='bold')
    ax.set_ylabel('Mean Value', fontsize=14, fontweight='bold')
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(layer_names, fontsize=12)
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_title(title, fontsize=16, fontweight='bold')

    ax.set_ylim(0, 3.5)


def create_composite_plot(data_dir, lobe):
    set_publication_style()

    response_types = [
        None, 'response_flat', None,
        'response_superficial_inc', 'response_middle_inc', 'response_deep_inc',
        'response_superficial_dec', 'response_middle_dec', 'response_deep_dec'
    ]

    plot_title = f'Pipeline output layer profiles - {lobe}'
    plot_filename = f'pipeline_output_layer_profiles_{lobe}'
    fig, axs = plt.subplots(3, 3, figsize=(20, 20))
    fig.suptitle(plot_title, fontsize=24, fontweight='bold', x=0.05, y=0.95, ha='left')

    for i, response_type in enumerate(response_types):
        row = i // 3
        col = i % 3
        
        if response_type is None:
            fig.delaxes(axs[row, col])
            continue
        
        ## mean_values_{response_type}_100columns.txt file creates plot for the whole brain 
        ## lobe_data.txt file creates plot for specifically that lobe only
        if lobe == 'brain':
            whole_brain_file_path = os.path.join(data_dir, response_type, f'mean_values_{response_type}_100columns.txt')
            whole_brain_data = np.loadtxt(whole_brain_file_path)
        elif lobe == 'frontal' or 'parietal' or 'temporal' or 'occipital':
            brain_lobe_file_path = os.path.join(data_dir, response_type, f'{lobe}_data.txt')
            brain_lobe_data = np.loadtxt(brain_lobe_file_path)
        
        highlight_layer = None
        if 'superficial' in response_type:
            highlight_layer = 'Superficial'
        elif 'middle' in response_type:
            highlight_layer = 'Middle'
        elif 'deep' in response_type:
            highlight_layer = 'Deep'
        
        if lobe == 'brain':
            plot_layer_profile(axs[row, col], whole_brain_data, response_type.replace('_', ' ').title(), highlight_layer)
        elif lobe == 'frontal' or 'parietal' or 'temporal' or 'occipital':
            plot_layer_profile(axs[row, col], brain_lobe_data, response_type.replace('_', ' ').title(), highlight_layer)

    # Add a legend
    handles = [plt.Rectangle((0,0),1,1,color='#555555', ec="k", alpha=0.7),
               plt.Rectangle((0,0),1,1,color='#4FADFF', ec="k", alpha=0.7)]
    labels = ['Normal Responses', 'Changed Responses']
    fig.legend(handles, labels, loc='upper right', bbox_to_anchor=(0.95, 0.95), fontsize=18)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(os.path.join(data_dir, plot_filename), dpi=600, bbox_inches='tight')
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Create violin plots for multiple responses and combines them together")
    parser.add_argument("--data_path", required = True, help = "Path to layersim_experiment_mri_vol2vol/analysis_output_smooth/")
    parser.add_argument("--lobe", type=str, choices=['brain', 'frontal', 'parietal', 'temporal', 'occipital'], required=True, 
                        help = "Path to layersim_experiment_mri_vol2vol/analysis_output_smooth/")

    args = parser.parse_args()

    create_composite_plot(args.data_path, args.lobe)