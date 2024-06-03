import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate graphs from benchmark CSV files.')
    parser.add_argument('benchmarks', metavar='B', type=str, nargs='+', help='List of benchmark names')
    parser.add_argument('-r', '--relative', action='store_true', help='Use relative values based on the lowest kernel version')
    return parser.parse_args()

def make_kernel_names(log_dir: str = './log') -> List[str]:
    try:
        files = os.listdir(log_dir)
        kernel_names = {file.split('--')[0] for file in files if file.endswith('-summary.csv')}
        logging.debug(f"Found kernel names: {kernel_names}")
        return list(kernel_names)
    except Exception as e:
        logging.error(f"Error while making kernel names: {e}")
        return []

def read_csv_data(kernel_name: str, benchmark: str, log_dir: str = './log') -> pd.DataFrame:
    try:
        file_path = os.path.join(log_dir, f"{kernel_name}--{benchmark}-summary.csv")
        logging.debug(f"Reading data from {file_path}")
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        return pd.DataFrame()

def extract_data(df: pd.DataFrame, category: str) -> float:
    try:
        assert not df.empty, "DataFrame is empty"
        filtered_df = df[df['Unnamed: 0'] == 'average']
        value = filtered_df[category].values[0]
        logging.debug(f"Extracted data for category {category}: {value}")
        return value
    except AssertionError as e:
        logging.error(f"Assertion error: {e}")
        return 0.0
    except Exception as e:
        logging.error(f"Error extracting data: {e}")
        return 0.0

def plot_data(data: Dict[str, Dict[str, float]], category: str, benchmarks: List[str], output_dir: str = './log', relative: bool = False):
    try:
        fig, ax = plt.subplots()
        bar_width = 0.2
        index = range(len(benchmarks))

        for i, (kernel_name, values) in enumerate(data.items()):
            bar_positions = [p + bar_width * i for p in index]
            ax.bar(bar_positions, [values[benchmark] for benchmark in benchmarks], bar_width, label=kernel_name)

        ax.set_xlabel('Benchmarks')
        ax.set_ylabel(category.capitalize())
        ax.set_title(f'{category.capitalize()} Benchmark Results')
        ax.set_xticks([p + bar_width * (len(data) / 2 - 0.5) for p in index])
        ax.set_xticklabels(benchmarks)
        ax.legend()

        if relative:
            ax.axhline(0.0, color='black', linewidth=0.8)

        # Create output file name
        suffix = '-relative.png' if relative else '.png'
        output_file = os.path.join(output_dir, '-'.join(benchmarks) + f'-{category}{suffix}')
        plt.savefig(output_file)
        logging.debug(f"Graph saved to {output_file}")
    except Exception as e:
        logging.error(f"Error plotting data: {e}")

def main():
    args = parse_arguments()
    categories = ["total", "real", "user", "sys"]
    log_dir = './log'

    kernel_names = make_kernel_names(log_dir)
    kernel_names.sort()  # Ensure kernel names are sorted for finding the lowest one
    logging.debug(f"Kernel names: {kernel_names}")

    for category in categories:
        category_data = {}
        min_values = {}

        for kernel_name in kernel_names:
            for benchmark in args.benchmarks:
                df = read_csv_data(kernel_name, benchmark, log_dir)
                if not df.empty:
                    value = extract_data(df, category)
                    if kernel_name not in category_data:
                        category_data[kernel_name] = {}
                    category_data[kernel_name][benchmark] = value

        if args.relative and kernel_names:
            min_kernel = kernel_names[0]
            for benchmark in args.benchmarks:
                if min_kernel in category_data and benchmark in category_data[min_kernel]:
                    min_value = category_data[min_kernel][benchmark]
                    min_values[benchmark] = min_value
                    for kernel_name in kernel_names[1:]:
                        if benchmark in category_data[kernel_name]:
                            category_data[kernel_name][benchmark] = (min_value - category_data[kernel_name][benchmark]) / min_value

            # Remove the minimum kernel from the data to be plotted
            if min_kernel in category_data:
                del category_data[min_kernel]

        plot_data(category_data, category, args.benchmarks, log_dir, args.relative)

if __name__ == "__main__":
    main()

