import os
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

def parse_output(output: str) -> Dict[str, float]:
    # Initialize total to 0 in case of failing benchmark
    result = {"total": 0}
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

def get_all_raw_files(directory: str) -> List[str]:
    """ Recursively get all raw files in the specified directory """
    raw_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith("-raw.txt"):  # or any other file pattern to identify raw files
                raw_path = os.path.join(root, file)
                raw_files.append(raw_path)
                logging.debug(f"Raw files found: {raw_path}")
    return raw_files

def main():
    log_path = get_config("log_path")
    raw_files = get_all_raw_files(log_path)

    for raw_file in raw_files:
        benchmark = raw_file.split('--')[1].split('-')[0]
        processed_file = raw_file.replace('-raw.txt', '-processed.csv')
        summary_file = raw_file.replace('-raw.txt', '-summary.csv')

        delete_file(processed_file)
        delete_file(summary_file)

        raw_content = parse_raw_file(raw_file)
        save_processed_output(processed_file, benchmark, raw_content)
        processed_content = parse_processed_file(processed_file)
        save_summary_output(summary_file, processed_content)

if __name__ == '__main__':
    main()

