import os
import argparse
import subprocess
import logging
import statistics
import csv
from typing import List, Dict
import matplotlib.pyplot as plt

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ExperimentConfig:
    def __init__(self, benchmarks: List[str], iterations: int = 1, mode: str = "both"):
        self.benchmarks = benchmarks
        self.iterations = iterations
        self.mode = mode
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

def create_directory(directory: str):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.debug(f"Directory created: {directory}")
    else:
        logging.debug(f"Directory already exists: {directory}")

def run_benchmark(benchmark: str, kernel_name: str, iterations: int) -> List[Dict[str, float]]:
    results = []
    for i in range(iterations):
        try:
            output = subprocess.check_output(f"parsecmgmt -a run -x pre -p {benchmark} -c gcc-hooks -i native", shell=True).decode()
            logging.debug(f"Benchmark output (iteration {i + 1}): {output}")
            
            result = parse_output(output)
            results.append(result)
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to run benchmark {benchmark} on iteration {i + 1}")
            raise e
    return results

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

def write_raw_output(filename: str, results: List[Dict[str, float]]):
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["iteration", "total", "real", "user", "sys"])
        for i, result in enumerate(results):
            writer.writerow([i + 1, result["total"], result["real"], result["user"], result["sys"]])
    logging.debug(f"Raw output written to {filename}")

def write_summary_output(filename: str, results: List[Dict[str, float]]):
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

def create_comparison_chart(results: Dict[str, Dict[str, float]], output_file: str):
    categories = ["total", "real", "user", "sys"]
    benchmarks = list(results.keys())
    kernel_names = list(results[benchmarks[0]].keys())

    for category in categories:
        for kernel_name in kernel_names:
            values = [results[benchmark][kernel_name][category] for benchmark in benchmarks]
            plt.bar(benchmarks, values, label=kernel_name)
        plt.xlabel('Benchmark')
        plt.ylabel(f'{category} time (s)')
        plt.title(f'Benchmark Comparison: {category}')
        plt.legend()
        plt.savefig(output_file.replace('.png', f'-{category}.png'))
        plt.close()
        logging.debug(f"Comparison chart for {category} saved to {output_file.replace('.png', f'-{category}.png')}")

def main():
    parser = argparse.ArgumentParser(description='Benchmark Execution and Analysis Tool')
    parser.add_argument('benchmarks', nargs='+', help='List of benchmarks to run')
    parser.add_argument('-i', '--iterations', type=int, default=1, help='Number of iterations (default: 1)')
    parser.add_argument('-m', '--mode', choices=['run', 'analyze', 'both'], default='both', help='Execution mode (default: both)')
    
    args = parser.parse_args()
    config = ExperimentConfig(args.benchmarks, args.iterations, args.mode)

    create_directory('runtime_experiment')

    benchmark_results = {}

    for benchmark in config.benchmarks:
        raw_file = f"runtime_experiment/{benchmark}-{config.kernel_name}-raw.csv"
        summary_file = f"runtime_experiment/{benchmark}-{config.kernel_name}-summary.csv"
        comparison_file = f"runtime_experiment/{config.kernel_name}-comparison.png"

        if config.mode in ['run', 'both']:
            results = run_benchmark(benchmark, config.kernel_name, config.iterations)
            write_raw_output(raw_file, results)
            benchmark_results[benchmark] = {
                config.kernel_name: {
                    "total": statistics.mean([r["total"] for r in results]),
                    "real": statistics.mean([r["real"] for r in results]),
                    "user": statistics.mean([r["user"] for r in results]),
                    "sys": statistics.mean([r["sys"] for r in results])
                }
            }

        if config.mode in ['analyze', 'both']:
            results = []
            with open(raw_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    results.append({
                        "total": float(row["total"]),
                        "real": float(row["real"]),
                        "user": float(row["user"]),
                        "sys": float(row["sys"])
                    })
            write_summary_output(summary_file, results)

    if config.mode in ['analyze', 'both']:
        create_comparison_chart(benchmark_results, comparison_file)

if __name__ == '__main__':
    main()

