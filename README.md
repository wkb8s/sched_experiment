# PARSEC Benchmark Execution and Analysis Tool

## Logging Tool
Run benchmarks and save logs as csv files.

```
usage: runtime_logger.py [-h] [-i ITERATIONS] [-m {run,analyze,both}]
                         benchmarks [benchmarks ...]

positional arguments:
  benchmarks            List of benchmarks to run

options:
  -h, --help            show this help message and exit
  -i ITERATIONS, --iterations ITERATIONS
                        Number of iterations (default: 1)
  -m {run,analyze,both}, --mode {run,analyze,both}
                        Execution mode (default: both)
```

### Visualizing Tool
Generate graphs from benchmark log CSV files.

```
usage: runtime_chartmaker.py [-h] [-r] B [B ...]

positional arguments:
  B               List of benchmark names

options:
  -h, --help      show this help message and exit
  -r, --relative  Use relative values based on the lowest kernel version
```
