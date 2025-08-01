import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os
from pathlib import Path


def analyze_stereoscope_data():
    #get all csv
    csv_files = glob.glob("responses/*.csv")

    if not csv_files:
        print("No CSV files found in the responses folder!")
        return

    print(f"Found {len(csv_files)} files to analyze")

    # storage
    all_data = []

    # output dir
    os.makedirs("individual_plots", exist_ok=True)

    # Process each file
    for i, file_path in enumerate(csv_files):
        print(f"Processing {file_path}...")
        df = pd.read_csv(file_path)

        # theta mag
        df['theta_magnitude'] = abs(df['left_theta'])
        grouped = df.groupby('theta_magnitude').agg({
            'reaction_time': ['mean', 'std', 'count'],
            'correct': ['mean', 'sum', 'count']
        }).round(4)

        grouped.columns = ['_'.join(col).strip() for col in grouped.columns]
        grouped = grouped.reset_index()
        grouped.rename(columns={
            'reaction_time_mean': 'mean_rt',
            'reaction_time_std': 'std_rt',
            'reaction_time_count': 'rt_count',
            'correct_mean': 'accuracy',
            'correct_sum': 'correct_trials',
            'correct_count': 'total_trials'
        }, inplace=True)

        # indiv plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        #Plot 1: Response Time vs Theta
        ax1.errorbar(grouped['theta_magnitude'], grouped['mean_rt'],
                     yerr=grouped['std_rt'], marker='o', capsize=5, capthick=2)
        ax1.set_xlabel('Theta Magnitude')
        ax1.set_ylabel('Mean Response Time (s)')
        ax1.set_title(f'Response Time vs Theta Magnitude\n{os.path.basename(file_path)}')
        ax1.grid(True, alpha=0.3)
        ax1.set_xscale('log')

        #Plot 2: Accuracy vs Theta
        ax2.plot(grouped['theta_magnitude'], grouped['accuracy'], marker='o', linewidth=2)
        ax2.set_xlabel('Theta Magnitude')
        ax2.set_ylabel('Accuracy')
        ax2.set_title(f'Accuracy vs Theta Magnitude\n{os.path.basename(file_path)}')
        ax2.grid(True, alpha=0.3)
        ax2.set_xscale('log')
        ax2.set_ylim(0, 1)

        plt.tight_layout()

        # indiv plot
        plot_filename = f"individual_plots/{os.path.basename(file_path).replace('.csv', '_analysis.png')}"
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        plt.close()
        grouped['participant'] = f"P{i + 1:02d}"
        grouped['filename'] = os.path.basename(file_path)
        all_data.append(grouped)

    # combined
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_accuracy = combined_df.groupby('theta_magnitude').agg({
        'correct_trials': 'sum',
        'total_trials': 'sum'
    })
    combined_accuracy['combined_accuracy'] = combined_accuracy['correct_trials'] / combined_accuracy['total_trials']
    combined_accuracy = combined_accuracy.reset_index()

    individual_accuracies = combined_df.pivot(index='theta_magnitude',
                                              columns='participant',
                                              values='accuracy')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Acccuracy curves (in gray for each person)
    for participant in individual_accuracies.columns:
        ax1.plot(individual_accuracies.index, individual_accuracies[participant],
                 alpha=0.3, color='gray', linewidth=1)

    # combined accuracy curve for everybody
    ax1.plot(combined_accuracy['theta_magnitude'], combined_accuracy['combined_accuracy'],
             marker='o', linewidth=3, color='red', markersize=8,
             label=f'Combined (N={len(csv_files)} participants)')

    ax1.set_xlabel('Theta Magnitude')
    ax1.set_ylabel('Accuracy')
    ax1.set_title('Accuracy vs Theta Magnitude - All Participants')
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')
    ax1.set_ylim(0, 1)
    ax1.legend()

    #combined accuracy + std error of mean as error bars
    accuracy_stats = combined_df.groupby('theta_magnitude')['accuracy'].agg(['mean', 'std', 'count'])
    accuracy_stats['sem'] = accuracy_stats['std'] / np.sqrt(accuracy_stats['count'])

    ax2.errorbar(accuracy_stats.index, accuracy_stats['mean'],
                 yerr=accuracy_stats['sem'], marker='o', capsize=5, capthick=2,
                 linewidth=2, markersize=8)
    ax2.set_xlabel('Theta Magnitude')
    ax2.set_ylabel('Mean Accuracy ± SEM')
    ax2.set_title('Mean Accuracy vs Theta Magnitude\n(Error bars show SEM across participants)')
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')
    ax2.set_ylim(0, 1)

    plt.tight_layout()
    plt.savefig('combined_accuracy_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

    # summary stats
    print("=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    print(f"Total participants analyzed: {len(csv_files)}")
    print(f"Theta magnitudes tested: {sorted(combined_accuracy['theta_magnitude'].unique())}")
    print("\nCombined Accuracy by Theta Magnitude:")
    print(combined_accuracy[['theta_magnitude', 'combined_accuracy', 'correct_trials', 'total_trials']].to_string(
        index=False))

    print(f"\nIndividual plots saved in: individual_plots/")
    print(f"Combined plot saved as: combined_accuracy_analysis.png")

    # combined to csv
    combined_df.to_csv('combined_analysis_data.csv', index=False)
    combined_accuracy.to_csv('combined_accuracy_summary.csv', index=False)
    print(f"Data saved to: combined_analysis_data.csv and combined_accuracy_summary.csv")


if __name__ == "__main__":
    analyze_stereoscope_data()