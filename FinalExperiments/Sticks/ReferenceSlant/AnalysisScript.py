import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from glob import glob
import os


def load_latest_data():
    try:
        csv_files = glob('responses/stereoscope_responses_*.csv')
        if not csv_files:
            print("No CSV files found in responses folder")
            return None
        latest_file = max(csv_files, key=os.path.getctime)
        print(f"Loading data from: {latest_file}")
        return pd.read_csv(latest_file)
    except Exception as e:
        print(f"Error loading data: {e}")
        return None


def calculate_accuracy_by_delta(df, reference_theta):
    ref_data = df[df['reference_theta'] == reference_theta].copy()

    # acc
    accuracy_stats = ref_data.groupby('delta_theta').agg({
        'correct': ['mean', 'count', 'std']
    }).round(3)

    #flatten names
    accuracy_stats.columns = ['accuracy', 'n_trials', 'accuracy_std']
    accuracy_stats = accuracy_stats.reset_index()

    #std error
    accuracy_stats['accuracy_sem'] = accuracy_stats['accuracy_std'] / np.sqrt(accuracy_stats['n_trials'])

    return accuracy_stats.sort_values('delta_theta')


def analyze_stereoscope_data():
    #load
    df = load_latest_data()
    if df is None:
        return

    print(f"Loaded {len(df)} trials")

    #get unique theta values
    reference_thetas = sorted(df['reference_theta'].unique())
    print(f"Reference theta values: {reference_thetas}")

    #get delta uniques
    delta_thetas = sorted(df['delta_theta'].unique())
    print(f"Delta theta values: {delta_thetas}")

    # plot part
    plt.figure(figsize=(10, 7))

    # curve per ref
    colors = plt.cm.Set1(np.linspace(0, 1, len(reference_thetas)))

    for i, ref_theta in enumerate(reference_thetas):
        accuracy_stats = calculate_accuracy_by_delta(df, ref_theta)

        #plot no error bars
        plt.plot(accuracy_stats['delta_theta'],
                 accuracy_stats['accuracy'],
                 marker='o',
                 markersize=8,
                 linewidth=2,
                 color=colors[i],
                 label=f'Reference θ = {ref_theta}°')

        #print summary
        print(f"\nReference Theta = {ref_theta}°:")
        for _, row in accuracy_stats.iterrows():
            print(
                f"  Δθ = {row['delta_theta']:+.2f}°: {row['accuracy']:.3f} ± {row['accuracy_sem']:.3f} (n={int(row['n_trials'])})")


    # Format
    plt.xlabel('Delta Theta (degrees)', fontsize=14)
    plt.ylabel('Proportion Correct', fontsize=14)
    plt.title('Psychometric Curves by Reference Theta', fontsize=16, fontweight='bold')
    plt.ylim(0, 1)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12)

    #overall stats
    overall_accuracy = df['correct'].mean()
    total_trials = len(df)

    stats_text = f'Overall Accuracy: {overall_accuracy:.3f}\nTotal Trials: {total_trials}'
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
             fontsize=11, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()

    # save
    plt.savefig('psychometric_curves_delta_theta.png', dpi=300, bbox_inches='tight')
    print(f"\nSaved plot: psychometric_curves_delta_theta.png")

    plt.show()



if __name__ == "__main__":
    analyze_stereoscope_data()