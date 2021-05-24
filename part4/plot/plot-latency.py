import os
import math

import numpy as np
import matplotlib.pyplot as plt

import parse

def plot_latency(results, groups):
    fig, ax = plt.subplots(dpi=100, figsize=(16, 9), tight_layout=True)

    for logs, group in zip(results, groups):
        # averaging across repetitions
        metrics = [log['metrics'] for log in logs]
        avg = np.mean(metrics, axis=0)
        err = np.std(metrics, axis=0) / math.sqrt(len(logs))

        ax.errorbar(avg[:, 0], avg[:, 1], xerr=err[:, 0], yerr=err[:, 1], label=group, fmt='o-',
             markersize=3, capsize=3, linewidth=1)

    ax.set_ylabel('P95 Latency (ms)', fontsize=16, labelpad=0.1)
    ax.set_xlabel('Achieved QPS', fontsize=16, labelpad=0.1)

    ax.set_ylim([0, 2.5])
    ax.set_xlim([0, 125000])

    x_ticks = list(range(0, 130000, 20000))
    x_ticks.append(125000)
    x_tick_labels = [str(x // 1000) + 'K' for x in x_ticks]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_tick_labels)
    plt.yticks(fontsize=14)
    plt.xticks(fontsize=14)

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.grid(True)

    ax.legend(fontsize=16)

    plt.savefig('latency-qps.png')
    plt.show()

def main(log_dir):
    configs = ['1T1C', '1T2C', '2T1C', '2T2C']
    results = list()
    for config in configs:
        file_path = os.path.join(log_dir, config + '.txt')
        results.append(parse.load_measurement_logs(file_path, repeat=True))

    plot_latency(results, configs)

if __name__ == '__main__':
    import sys
    main(sys.argv[1])

