## Plotting violin plots for increased and decreased responses of each lobe together

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

def plot_layer_profile(ax, data, title, highlight_layer, lobe_color):
    layer_names = ['Superficial', 'Middle', 'Deep']
    default_color = lobe_color[0]  # Darker shade
    highlight_color = lobe_color[1]  # Lighter shade
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

    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(layer_names, fontsize=12)
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_title(title, fontsize=16, fontweight='bold')

    ax.set_ylim(0, 3.5)


def create_composite_plot(data_dir):
    set_publication_style()

    lobes = ['Frontal', 'Parietal', 'Temporal', 'Occipital']
    layers = ['Superficial', 'Middle', 'Deep']
    responses = ['inc', 'dec']

    # Define colors for each lobe (dark and light shades)
    lobe_colors = {
        'Frontal': ('#8B0000', '#FF6666'),    # Dark red, Light red
        'Parietal': ('#00008B', '#6666FF'),   # Dark blue, Light blue
        'Temporal': ('#006400', '#66FF66'),   # Dark green, Light green
        'Occipital': ('#8B008B', '#FF66FF'),  # Dark purple, Light purple
    }

    fig, axs = plt.subplots(3, 4, figsize=(20, 15))
    fig.suptitle('Responses Across Layers and Lobes', fontsize=24, fontweight='bold', y=1.02)

    for i, layer in enumerate(layers):
        for j, lobe in enumerate(lobes):
            ax = axs[i, j]
            
            for response in responses:
                file_path = os.path.join(data_dir, f'response_{layer.lower()}_{response}', f'{lobe.lower()}_data.txt')
                if os.path.exists(file_path):
                    data = np.loadtxt(file_path)
                    plot_layer_profile(ax, data, f'{lobe} Lobe', layer, lobe_colors[lobe])
            
            if i == 2:  # Only add x-label to bottom row
                ax.set_xlabel('Layer', fontsize=12, fontweight='bold')
            if j == 0:  # Only add y-label to left column
                ax.set_ylabel('Mean Value', fontsize=12, fontweight='bold')
            
            ax.set_title(f'{lobe} Lobe', fontsize=14, fontweight='bold')
            ax.set_ylim(0, 3.5)

    # Add row labels
    for i, layer in enumerate(layers):
        fig.text(-0.01, 0.75 - i*0.25, layer, rotation=90, fontsize=16, fontweight='bold', va='center')

    # Add a legend
    legend_elements = [plt.Rectangle((0,0),1,1,fc=colors[0], ec="k", alpha=0.7, label=f'{lobe} Normal')
                       for lobe, colors in lobe_colors.items()]
    legend_elements += [plt.Rectangle((0,0),1,1,fc=colors[1], ec="k", alpha=0.7, label=f'{lobe} Changed')
                        for lobe, colors in lobe_colors.items()]
    fig.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.95, 0.95), 
               ncol=4, fontsize=10, frameon=True, edgecolor='black')

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    filename = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(data_dir))))
    plt.savefig(os.path.join(data_dir, f'{filename}_composite_layer_profiles.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Plotting violin plots for increased or decreased responses of each lobe together")
    parser.add_argument("--data_path", required = True, help = "Path to layersim_experiment_mri_vol2vol/analysis_output_smooth/")

    args = parser.parse_args()

    create_composite_plot(args.data_path)