import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import logging
from datetime import datetime, timedelta
from typing import Tuple, List

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

def parse_filename(filename: str) -> Tuple[str, str]:
    """
    Parses the filename to extract kernel and benchmark names.
    
    Args:
    filename (str): The name of the CSV file.
    
    Returns:
    Tuple[str, str]: A tuple containing the kernel and benchmark names.
    """
    assert isinstance(filename, str), "Filename must be a string"
    
    base_name = os.path.basename(filename)
    kernel_benchmark = base_name.split('--')
    if len(kernel_benchmark) != 2:
        logging.error(f"Invalid filename format: {filename}")
        raise ValueError("Filename must be in the format '<kernel name>--<benchmark name>-cpuusage.csv'")
    
    kernel = kernel_benchmark[0]
    benchmark = kernel_benchmark[1].replace('-cpuusage.csv', '')
    logging.debug(f"Parsed kernel: {kernel}, benchmark: {benchmark} from filename: {filename}")
    
    return kernel, benchmark

def load_and_process_csv(filename: str) -> Tuple[pd.DataFrame, int]:
    """
    Loads the CSV file and processes it to extract CPU usage data.
    
    Args:
    filename (str): The path to the CSV file.
    
    Returns:
    Tuple[pd.DataFrame, int]: A DataFrame containing the processed CPU usage data,
                              and the number of CPUs.
    """
    assert isinstance(filename, str), "Filename must be a string"
    
    try:
        df = pd.read_csv(filename, parse_dates=['Timestamp'])
        logging.debug(f"CSV loaded successfully with shape: {df.shape}")
        
        # Calculate elapsed time in seconds from the first timestamp
        df['Elapsed time (s)'] = (df['Timestamp'] - df['Timestamp'].iloc[0]).dt.total_seconds()
        
        # Drop the Timestamp column as we now have 'Elapsed time (s)'
        df = df.drop(columns=['Timestamp'])
        
        # Determine the number of CPUs based on the columns
        num_cpus = len(df.columns) - 1  # Subtract 1 for the 'Elapsed time (s)' column
        
        logging.debug(f"Processed DataFrame with elapsed time. Number of CPUs: {num_cpus}")
        
        return df, num_cpus
    
    except Exception as e:
        logging.error(f"Error processing file {filename}: {e}")
        raise

def plot_heatmap(df: pd.DataFrame, num_cpus: int, kernel: str, benchmark: str) -> None:
    """
    Generates a heatmap of CPU usage over time.
    
    Args:
    df (pd.DataFrame): The DataFrame containing CPU usage data.
    num_cpus (int): The number of CPUs.
    kernel (str): The kernel name.
    benchmark (str): The benchmark name.
    """
    assert isinstance(df, pd.DataFrame), "Input must be a pandas DataFrame"
    assert isinstance(num_cpus, int) and num_cpus > 0, "Number of CPUs must be a positive integer"
    assert isinstance(kernel, str), "Kernel name must be a string"
    assert isinstance(benchmark, str), "Benchmark name must be a string"
    
    plt.figure(figsize=(12, num_cpus))
    
    # Extract the CPU usage columns
    cpu_usage_data = df[[f'CPU {i} (%)' for i in range(num_cpus)]].T
    
    # Create the heatmap
    sns.heatmap(cpu_usage_data, cmap="YlGnBu", cbar_kws={'label': 'CPU Usage (%)'})
    
    # Configure the plot
    plt.title(f'CPU Usage Heatmap for {kernel} - {benchmark}')
    plt.xlabel('Elapsed time (s)')
    plt.ylabel('CPU Number')
    plt.yticks(np.arange(0.5, num_cpus, 1), labels=[f'CPU {i}' for i in range(num_cpus)], rotation=0)
    plt.xticks(rotation=45)
    
    output_filename = f'./log/{kernel}--{benchmark}-cpuusage.png'
    plt.savefig(output_filename, bbox_inches='tight')
    logging.info(f"Heatmap saved to {output_filename}")
    plt.close()

def process_csv_to_heatmap(filename: str) -> None:
    """
    Main function to process a CSV file and generate a heatmap.
    
    Args:
    filename (str): The name of the CSV file.
    """
    logging.info(f"Processing file: {filename}")
    kernel, benchmark = parse_filename(filename)
    df, num_cpus = load_and_process_csv(filename)
    plot_heatmap(df, num_cpus, kernel, benchmark)

def find_csv_files(directory: str) -> List[str]:
    """
    Finds all CSV files in a given directory (not including subdirectories).
    
    Args:
    directory (str): The directory to search for CSV files.
    
    Returns:
    List[str]: A list of file paths to CSV files.
    """
    assert isinstance(directory, str), "Directory path must be a string"
    
    try:
        csv_files = [
            os.path.join(directory, file)
            for file in os.listdir(directory)
            if file.endswith('-cpuusage.csv') and os.path.isfile(os.path.join(directory, file))
        ]
        logging.debug(f"Found {len(csv_files)} CSV files in directory: {directory}")
    except Exception as e:
        logging.error(f"Error finding CSV files in directory {directory}: {e}")
        raise
    
    return csv_files

def main():
    """
    Main function to process all CSV files in the ./log directory.
    """
    try:
        csv_directory = './log'
        csv_files = find_csv_files(csv_directory)
        
        if not csv_files:
            logging.warning(f"No CSV files found in directory: {csv_directory}")
            return
        
        for csv_file in csv_files:
            try:
                process_csv_to_heatmap(csv_file)
            except Exception as e:
                logging.error(f"Failed to process {csv_file}: {e}")
    
    except Exception as e:
        logging.critical(f"Critical error in main processing: {e}")

if __name__ == "__main__":
    main()

