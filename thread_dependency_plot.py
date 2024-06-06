import os
import argparse
import logging
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def create_directory(directory: str):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.debug(f"Directory created: {directory}")
    else:
        logging.debug(f"Directory already exists: {directory}")

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate benchmark graphs.")
    parser.add_argument('benchmarks', nargs='+', help='List of benchmark names')
    return parser.parse_args()

def get_latest_dirs(log_dir: str) -> Dict[int, str]:
    """Get the latest directories for each thread number."""
    latest_dirs = {}
    for subdir in os.listdir(log_dir):
        if subdir.count('-t') == 1:
            try:
                date_str, thread_num_str = subdir.rsplit('-t', 1)
                if not date_str.replace("-", "").isdigit() or not thread_num_str.isdigit():
                    continue
                thread_num = int(thread_num_str)
                date = datetime.strptime(date_str, '%Y-%m-%d')
                if thread_num not in latest_dirs or date > latest_dirs[thread_num][0]:
                    latest_dirs[thread_num] = (date, os.path.join(log_dir, subdir))
            except ValueError:
                logging.warning(f"Skipping invalid directory: {subdir}")
    return {k: v[1] for k, v in latest_dirs.items()}

def load_data(log_dir: str, benchmarks: List[str]) -> Dict[str, Dict[str, pd.DataFrame]]:
    """Load benchmark data from CSV files."""
    data = {}
    latest_dirs = get_latest_dirs(log_dir)
    if not latest_dirs:
        logging.error("No valid directories found.")
        raise RuntimeError("No valid directories found.")
    
    for benchmark in benchmarks:
        data[benchmark] = {}
        for thread_num, subdir in latest_dirs.items():
            for file in os.listdir(subdir):
                if file.endswith(f'{benchmark}-summary.csv'):
                    kernel_version = file.split('--')[0]
                    if kernel_version not in data[benchmark]:
                        data[benchmark][kernel_version] = {}
                    df = pd.read_csv(os.path.join(subdir, file), index_col=0)
                    df['#threads'] = thread_num
                    for mode in df.columns:
                        if mode not in data[benchmark][kernel_version]:
                            data[benchmark][kernel_version][mode] = pd.DataFrame()
                        data[benchmark][kernel_version][mode] = pd.concat([data[benchmark][kernel_version][mode], df.loc[['average'], [mode, '#threads']]])
    return data

def plot_data(log_dir: str, data: Dict[str, Dict[str, pd.DataFrame]], benchmarks: List[str]):
    """Plot the data for each benchmark and mode."""
    modes = ['total', 'real', 'user', 'sys']
    colors = plt.get_cmap('tab10')
    kernel_versions = sorted({kernel for benchmark_data in data.values() for kernel in benchmark_data})
    color_map = {kernel: colors(i % 10) for i, kernel in enumerate(kernel_versions)}
    
    for benchmark in benchmarks:
        for mode in modes:
            plt.figure()
            for kernel_version, mode_data in data[benchmark].items():
                if mode in mode_data:
                    df = mode_data[mode]
                    df.sort_values(by='#threads', inplace=True)
                    plt.plot(df['#threads'], df[mode], label=kernel_version, marker='o', color=color_map[kernel_version])
            plt.xlabel('#threads')
            plt.ylabel('Execution time (s)')
            plt.title(f'{benchmark} - {mode}')
            plt.legend()
            plt.grid(True)
            save_path = log_dir + '/fig_thread_dependency'
            create_directory(save_path)
            plt.savefig(f'{save_path}/{mode}_{benchmark}.png')
            plt.close()

def main():
    # Parse arguments
    args = parse_args()
    
    # Directory containing log data
    log_dir = './log'
    
    # Load data
    try:
        data = load_data(log_dir, args.benchmarks)
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        return
    
    # Plot data
    plot_data(log_dir, data, args.benchmarks)

if __name__ == '__main__':
    main()

