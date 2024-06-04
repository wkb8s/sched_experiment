import psutil
import time
import csv
import logging
from typing import List, Optional

def configure_logging(mode: str):
    """
    Configure logging based on the output mode.

    Args:
        mode (str): The output mode, either 'normal' or 'silent'.
    """
    if mode == 'silent':
        logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_parsecmgmt_pid() -> Optional[int]:
    """
    Get the PID of the 'parsecmgmt' process.
    
    Returns:
        Optional[int]: The PID of 'parsecmgmt' if found, else None.
    """
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == 'parsecmgmt':
            logging.debug(f"Found parsecmgmt with PID {proc.info['pid']}")
            return proc.info['pid']
    return None

def wait_for_parsecmgmt() -> int:
    """
    Wait until the 'parsecmgmt' process is found and return its PID.
    
    Returns:
        int: The PID of 'parsecmgmt'.
    """
    logging.info("Waiting for parsecmgmt process to start...")
    pid = get_parsecmgmt_pid()
    while pid is None:
        time.sleep(1)  # Wait for 1 second before checking again
        pid = get_parsecmgmt_pid()
    logging.info(f"parsecmgmt process started with PID {pid}")
    return pid

def get_process_group(pid: int) -> List[psutil.Process]:
    """
    Get the process group for a given PID.
    
    Args:
        pid (int): The PID of the parent process.
    
    Returns:
        List[psutil.Process]: A list of psutil.Process objects representing the process group.
    """
    assert isinstance(pid, int), "PID must be an integer."
    
    try:
        process = psutil.Process(pid)
        children = process.children(recursive=True)
        process_group = [process] + children
        logging.debug(f"Process group for PID {pid}: {[p.pid for p in process_group]}")
        for p in process_group:
            print(f"Process PID: {p.pid}, Name: {p.name()}")
        return process_group
    except psutil.NoSuchProcess:
        logging.error(f"No such process with PID {pid}.")
        return []

def monitor_cpu_usage(pid: int, interval: float = 1.0, log_file: str = './log/cpu_usage.csv'):
    """
    Monitor the CPU usage of a process group and log the results to a CSV file.
    
    Args:
        pid (int): The PID of the parent process.
        interval (float): The interval in seconds between each CPU usage check.
        log_file (str): The path to the CSV file for logging CPU usage.
    """
    assert isinstance(pid, int), "PID must be an integer."
    assert isinstance(interval, (int, float)) and interval > 0, "Interval must be a positive number."
    assert isinstance(log_file, str), "Log file path must be a string."
    
    process_group = get_process_group(pid)
    if not process_group:
        logging.error("No process group found. Exiting.")
        return

    cpu_count = psutil.cpu_count()
    
    try:
        with open(log_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            header = ['Timestamp'] + [f'CPU {i} (%)' for i in range(cpu_count)]
            writer.writerow(header)

            while psutil.pid_exists(pid):
                cpu_usages = [proc.cpu_percent(interval=0) for proc in process_group if proc.is_running()]
                time.sleep(interval)
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                cpu_percentages = psutil.cpu_percent(percpu=True)
                writer.writerow([timestamp] + cpu_percentages)
                logging.info(f"Timestamp: {timestamp}, CPU Usages: {cpu_percentages}")
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def main(log_file: str = './log/cpu_usage.csv', interval: float = 1.0, mode: str = 'normal'):
    configure_logging(mode)
    pid = get_parsecmgmt_pid()
    if pid is None:
        pid = wait_for_parsecmgmt()
    monitor_cpu_usage(pid, interval, log_file)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Monitor CPU usage of the parsecmgmt process group.')
    parser.add_argument('-l', '--log_file', type=str, default='./log/cpu_usage.csv', help='Path to the CSV log file')
    parser.add_argument('-i', '--interval', type=float, default=1.0, help='Interval in seconds between each CPU usage check')
    parser.add_argument('-m', '--mode', type=str, choices=['normal', 'silent'], default='normal', help='Output mode: normal or silent')
    args = parser.parse_args()

    main(log_file=args.log_file, interval=args.interval, mode=args.mode)

