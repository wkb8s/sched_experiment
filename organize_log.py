import os
import logging
import shutil
import argparse

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def main(results_dir: str, log_dir: str):
    """ Main function to organize log files based on benchmark names derived from file names """
    # Convert provided directories to absolute paths
    results_dir = os.path.abspath(results_dir)
    log_dir = os.path.abspath(log_dir)

    logging.debug(f"Using results directory: {results_dir}")
    logging.debug(f"Using log directory: {log_dir}")

    if not os.path.exists(log_dir):
        logging.debug(f"Creating log directory: {log_dir}")
        os.makedirs(log_dir)

    # Process files
    filename_heads = get_filename_heads(results_dir)

    for filename_head in filename_heads:
        err_file = f"{filename_head}-err.txt"
        if not is_empty_file(err_file):
            logging.error(f"Error file is not empty: {err_file}")
            continue
        
        try:
            # Extract details from the filename head
            date, time, kernel_name, benchmark_name, thread_num = parse_filename_head(filename_head)
            logging.debug(f"Parsed filename head - Date: {date}, Time: {time}, Kernel: {kernel_name}, Benchmark: {benchmark_name}, Threads: {thread_num}")

            # Create target directory based on the date and thread number
            target_dir = os.path.join(log_dir, f"{date}-t{thread_num}")
            if not os.path.exists(target_dir):
                logging.debug(f"Creating target directory: {target_dir}")
                os.makedirs(target_dir)

            # Define the source and destination file paths
            src_file = f"{filename_head}-result.txt"
            dest_file = os.path.join(target_dir, f"{kernel_name}--{benchmark_name}-raw.txt")
            logging.debug(f"Copying {src_file} to {dest_file}")

            # Copy the result file to the new location with the new name
            shutil.copy(src_file, dest_file)

            # Define the source and destination file paths
            last_index = filename_head.rfind('-')
            filename_head = filename_head[:last_index]
            src_file = f"{filename_head}-usage.csv"
            dest_file = os.path.join(target_dir, f"{kernel_name}--{benchmark_name}-cpuusage.csv")
            logging.debug(f"Copying {src_file} to {dest_file}")

            # Copy the result file to the new location with the new name
            shutil.copy(src_file, dest_file)

        except Exception as e:
            logging.error(f"Failed to process {filename_head}: {str(e)}")

def get_filename_heads(directory: str):
    """Get the list of filename heads from the specified directory."""
    try:
        filename_heads = []
        for filename in os.listdir(directory):
            if filename.endswith('-result.txt'):
                head = os.path.join(directory, filename[:-len('-result.txt')])
                filename_heads.append(head)
        logging.debug(f"Filename heads found: {filename_heads}")
        return filename_heads
    except Exception as e:
        logging.error(f"Error accessing directory {directory}: {str(e)}")
        return []

def is_empty_file(file_path: str):
    """Check if a file is empty."""
    try:
        is_empty = os.path.getsize(file_path) == 0
        logging.debug(f"File '{file_path}' is {'empty' if is_empty else 'not empty'}.")
        return is_empty
    except Exception as e:
        logging.error(f"Error checking file size for {file_path}: {str(e)}")
        return False

def parse_filename_head(filename_head: str):
    """Parse the filename head to extract date, time, kernel name, benchmark name, and thread number."""
    try:
        # Extract parts from the filename head
        parts = os.path.basename(filename_head).split('-')
        
        # Construct the date and time
        date = f"{parts[0][:4]}-{parts[0][4:6]}-{parts[0][6:]}"
        time = f"{parts[1][:2]}:{parts[1][2:]}"
        
        # Kernel name can contain dashes, so we need to join parts properly
        kernel_parts = parts[2:-3]
        kernel_name = '-'.join(kernel_parts)
        
        # Benchmark name and thread number are straightforward
        benchmark_name = parts[-3]
        thread_num = parts[-2]

        # Debug assertion to ensure the correct extraction
        assert benchmark_name not in kernel_parts, "Benchmark name appears to be part of kernel name"

        return date, time, kernel_name, benchmark_name, thread_num
    except IndexError as e:
        logging.error(f"Error parsing filename head {filename_head}: {str(e)}")
        raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Organize log files based on benchmark names.")
    parser.add_argument('results_dir', help='Directory containing the result files.')
    parser.add_argument('log_dir', help='Directory where organized logs will be saved.')
    args = parser.parse_args()

    # Run the main function
    main(args.results_dir, args.log_dir)

