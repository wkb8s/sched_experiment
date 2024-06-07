import csv
import logging
import argparse
import threading
import subprocess
import statistics
import cpuusage_monitor
from typing import List, Dict
import matplotlib.pyplot as plt
from utils.exectime_logging_util import *

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ExperimentConfig:
    def __init__(self, benchmarks: List[str], iterations: int = 1, threads: int = 1, mode: str = "both", inputset: str = "native"):
        self.benchmarks = benchmarks
        self.iterations = iterations
        self.threads = threads
        self.mode = mode
        self.inputset = inputset
        self.kernel_name = self.get_kernel_name()
    
    @staticmethod
    def get_kernel_name() -> str:
        try:
            kernel_name = subprocess.check_output("uname -r", shell=True).decode().strip()
            logging.debug(f"Kernel name: {kernel_name}")
            return kernel_name
        except subprocess.CalledProcessError as e:
            logging.error("Failed to get kernel name")
            raise e

def repeat_benchmark(raw_file: str, benchmark: str, config: ExperimentConfig):
    iterations = config.iterations
    inputset = config.inputset
    for i in range(iterations):
        output = run_benchmark_once(raw_file, benchmark, i, config)
        save_raw_output(raw_file, benchmark, output)

def run_benchmark_once(raw_file: str, benchmark: str, benchmark_iter: int, config: ExperimentConfig) -> str:
    try:
        inputset = config.inputset
        threads = config.threads
        exec_cmd = f"parsecmgmt -a run -x pre -p {benchmark} -n {threads} -c gcc-hooks -i {inputset}"
        monitor_thread = threading.Thread(target=cpuusage_monitor.main, args=(f"./log/{config.kernel_name}--{benchmark}-cpuusage.csv", 1.0, "silent"))
        monitor_thread.start()
        logging.debug("Execute: " + exec_cmd)
        output = subprocess.check_output(exec_cmd, shell=True).decode()
        monitor_thread.join()
        logging.debug(f"Benchmark output (iteration {benchmark_iter + 1}): {output}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to run benchmark {benchmark} on iteration {benchmark_iter + 1}")
        raise e
    return output

def parse_output(output: str) -> Dict[str, float]:
    result = {}
    for line in output.split('\n'):
        if line.startswith("real"):
            result["real"] = parse_time(line.split()[1])
        elif line.startswith("user"):
            result["user"] = parse_time(line.split()[1])
        elif line.startswith("sys"):
            result["sys"] = parse_time(line.split()[1])
        elif "Total time spent in ROI" in line:
            result["total"] = float(line.split()[-1].replace('s', ''))
    logging.debug(f"Parsed result: {result}")
    return result

def parse_time(time_str: str) -> float:
    minutes, seconds = time_str.split('m')
    return float(minutes) * 60 + float(seconds.replace('s', ''))

def parse_raw_file(file_path: str) -> List[Dict[str, float]]:
    section_delimiter = "[PARSEC] [----------    End of output    ----------]"
    output_start_marker = "[PARSEC] [---------- Beginning of output ----------]"
    results = []
    with open(file_path, 'r') as file:
        content = file.read()
    sections = content.split(section_delimiter)
    for section in sections:
        if output_start_marker in section:
            output = section.split(output_start_marker)[1].strip()
            result = parse_output(output)
            if result:
                results.append(result)
    return results

def parse_processed_file(file_path: str) -> List[Dict[str, float]]:
    results = []
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                "total": float(row["total"]),
                "real": float(row["real"]),
                "user": float(row["user"]),
                "sys": float(row["sys"])
            })
    return results

def save_raw_output(filename: str, benchmark: str, output: str):
    with open(filename, 'a') as f:
        f.write(output)
        f.write('\n') # add a newline character for better readability
    logging.debug(f"Raw output written to {filename}")

def save_processed_output(filename: str, benchmark: str, results: List[Dict[str, float]]):
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["iteration", "total", "real", "user", "sys"])
        for i, result in enumerate(results):
            writer.writerow([i + 1, result["total"], result["real"], result["user"], result["sys"]])
    logging.debug(f"Processed output written to {filename}")

def save_summary_output(filename: str, results: List[Dict[str, float]]):
    summary = {
        "total": [r["total"] for r in results],
        "real": [r["real"] for r in results],
        "user": [r["user"] for r in results],
        "sys": [r["sys"] for r in results]
    }

    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["", "total", "real", "user", "sys"])
        writer.writerow(["average", statistics.mean(summary["total"]), statistics.mean(summary["real"]),
                         statistics.mean(summary["user"]), statistics.mean(summary["sys"])])
        writer.writerow(["max", max(summary["total"]), max(summary["real"]),
                         max(summary["user"]), max(summary["sys"])])
        writer.writerow(["min", min(summary["total"]), min(summary["real"]),
                         min(summary["user"]), min(summary["sys"])])
        writer.writerow(["stdev", statistics.stdev(summary["total"]) if len(summary["total"]) > 1 else 0,
                         statistics.stdev(summary["real"]) if len(summary["real"]) > 1 else 0,
                         statistics.stdev(summary["user"]) if len(summary["user"]) > 1 else 0,
                         statistics.stdev(summary["sys"]) if len(summary["sys"]) > 1 else 0])
    logging.debug(f"Summary output written to {filename}")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Run benchmarks and save logs as csv files.')
    parser.add_argument('benchmarks', nargs='+', help='List of benchmarks to run')
    parser.add_argument('-r', '--repeat', type=int, default=1, help='Number of repetitions (default: 1)')
    parser.add_argument('-t', '--threads', type=int, default=1, help='Number of threads (default: 1)')
    parser.add_argument('-m', '--mode', choices=['run', 'analyze', 'both'], default='both', help='Execution mode (default: both)')
    parser.add_argument('-i', '--inputset', choices=['test', 'native'], default='native', help='Input set (default: native)')
    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()
    config = ExperimentConfig(args.benchmarks, args.repeat, args.threads, args.mode, args.inputset)

    log_path = get_config("log_path")
    create_directory(log_path)

    for benchmark in config.benchmarks:
        raw_file = f"{log_path}/{config.kernel_name}--{benchmark}-raw.txt"
        processed_file = f"{log_path}/{config.kernel_name}--{benchmark}-processed.csv"
        summary_file = f"{log_path}/{config.kernel_name}--{benchmark}-summary.csv"

        if config.mode in ['run', 'both']:
            delete_file(raw_file)
            delete_file(processed_file)
            delete_file(summary_file)
            repeat_benchmark(raw_file, benchmark, config)

        if config.mode in ['analyze', 'both']:
            delete_file(processed_file)
            delete_file(summary_file)
            raw_content = parse_raw_file(raw_file)
            save_processed_output(processed_file, benchmark, raw_content)
            processed_content = parse_processed_file(processed_file)
            save_summary_output(summary_file, processed_content)

if __name__ == '__main__':
    main()

